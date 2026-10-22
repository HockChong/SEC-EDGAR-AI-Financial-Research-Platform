"""PostgreSQL coordination and append-only ingestion history."""

import json
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import Engine, text

from sec_research.contracts.sec import IngestionCode, IngestionError, Source
from sec_research.ingestion.ports import Fetch


class PostgresManifest:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def begin_run(self, run_id: UUID, config: Mapping[str, object]) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("""
                INSERT INTO ingestion_runs (id, status, config)
                VALUES (:id, 'running', CAST(:config AS jsonb))
            """),
                {"id": run_id, "config": json.dumps(dict(config), default=str)},
            )

    def finish_run(self, run_id: UUID, *, failed: bool) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("""
                UPDATE ingestion_runs SET status=:status, finished_at=clock_timestamp()
                WHERE id=:id
            """),
                {"id": run_id, "status": "failed" if failed else "succeeded"},
            )

    @contextmanager
    def claim(self, source: Source) -> Iterator[None]:
        # Session locks survive intermediate manifest commits and release on connection loss.
        with self.engine.connect() as connection:
            acquired = connection.execute(
                text("SELECT pg_try_advisory_lock(hashtextextended(:url, 2702))"),
                {"url": source.url},
            ).scalar_one()
            connection.commit()
            if not acquired:
                raise IngestionError(IngestionCode.BUSY, retryable=True)
            try:
                yield
            finally:
                connection.execute(
                    text("SELECT pg_advisory_unlock(hashtextextended(:url, 2702))"),
                    {"url": source.url},
                )
                connection.commit()

    def latest(self, source: Source) -> Fetch | None:
        with self.engine.connect() as connection:
            record = connection.execute(
                text("""
                SELECT record FROM ingestion_fetches WHERE source_url=:url
                AND record->>'processing_status' = 'unprocessed'
                ORDER BY fetched_at DESC, id DESC LIMIT 1
            """),
                {"url": source.url},
            ).scalar_one_or_none()
        return Fetch.model_validate(record) if record is not None else None

    def start(self, source: Source, run_id: UUID) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("""
                INSERT INTO ingestion_sources (url, metadata, status, attempts)
                VALUES (:url, CAST(:metadata AS jsonb), 'downloading', 1)
                ON CONFLICT (url) DO UPDATE SET status='downloading',
                    attempts=ingestion_sources.attempts+1, error_code=NULL,
                    updated_at=clock_timestamp()
            """),
                {"url": source.url, "metadata": source.model_dump_json()},
            )
            # A durable start event makes interrupted operations visible.
            connection.execute(
                text("""
                INSERT INTO ingestion_attempts
                    (run_id, source_url, status, retryable, http_attempts)
                VALUES (:run, :url, 'started', true, 0)
            """),
                {"run": run_id, "url": source.url},
            )

    def complete(self, fetch: Fetch) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("""
                INSERT INTO ingestion_fetches (id, run_id, source_url, fetched_at, sha256, record)
                VALUES (:id, :run, :url, :at, :hash, CAST(:record AS jsonb))
            """),
                {
                    "id": fetch.id,
                    "run": fetch.run_id,
                    "url": fetch.source.url,
                    "at": fetch.fetched_at,
                    "hash": fetch.sha256,
                    "record": fetch.model_dump_json(),
                },
            )
            status = "quarantined" if fetch.processing_status == "quarantined" else "succeeded"
            connection.execute(
                text("""
                UPDATE ingestion_sources SET status=:status, error_code=NULL,
                    updated_at=clock_timestamp() WHERE url=:url
            """),
                {"status": status, "url": fetch.source.url},
            )
            connection.execute(
                text("""
                INSERT INTO ingestion_attempts
                    (run_id, source_url, status, retryable, http_attempts)
                VALUES (:run, :url, :status, false, :attempts)
            """),
                {
                    "run": fetch.run_id,
                    "url": fetch.source.url,
                    "status": status,
                    "attempts": fetch.attempts,
                },
            )

    def fail(self, source: Source, run_id: UUID, error: IngestionError) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text("""
                UPDATE ingestion_sources SET status='failed', error_code=:code,
                    updated_at=clock_timestamp() WHERE url=:url
            """),
                {"code": error.code.value, "url": source.url},
            )
            connection.execute(
                text("""
                INSERT INTO ingestion_attempts
                    (run_id, source_url, status, error_code, retryable, http_attempts)
                VALUES (:run, :url, 'failed', :code, :retryable, :attempts)
            """),
                {
                    "run": run_id,
                    "url": source.url,
                    "code": error.code.value,
                    "retryable": error.retryable,
                    "attempts": error.attempts,
                },
            )

    def all_fetches(self) -> list[Fetch]:
        with self.engine.connect() as connection:
            records = connection.execute(text("SELECT record FROM ingestion_fetches ORDER BY id"))
            return [Fetch.model_validate(record) for record in records.scalars()]


class PostgresLimiter:
    """One aggregate start interval per database, across hosts/processes and both SEC hosts."""

    def __init__(self, engine: Engine, rate: float = 5) -> None:
        if not 0 < rate <= 5:
            raise ValueError("rate must be greater than zero and at most five")
        self.engine, self.interval = engine, 1 / rate

    def wait(self, deadline: float) -> None:
        with self.engine.begin() as connection:
            # A nonblocking advisory lock avoids an unbounded wait behind another worker.
            while not connection.execute(
                text("SELECT pg_try_advisory_xact_lock(2702001)")
            ).scalar_one():
                if time.monotonic() + 0.02 >= deadline:
                    raise IngestionError(IngestionCode.DEADLINE, retryable=True)
                time.sleep(0.02)
            delay = connection.execute(
                text("""
                SELECT GREATEST(0, EXTRACT(EPOCH FROM next_request-clock_timestamp()))
                FROM sec_rate_limit WHERE singleton
            """)
            ).scalar_one()
            if time.monotonic() + float(delay) >= deadline:
                raise IngestionError(IngestionCode.DEADLINE, retryable=True)
            time.sleep(float(delay))
            connection.execute(
                text("""
                UPDATE sec_rate_limit SET next_request=clock_timestamp() +
                    (:interval * interval '1 second') WHERE singleton
            """),
                {"interval": self.interval},
            )
