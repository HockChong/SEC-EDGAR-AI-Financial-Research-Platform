import json
import time
from collections.abc import Mapping
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from sec_research.adapters.postgres.database import create_database_engine
from sec_research.adapters.postgres.ingestion import PostgresLimiter, PostgresManifest
from sec_research.adapters.sec.client import Response
from sec_research.adapters.storage.local import LocalBronze
from sec_research.contracts.sec import IngestionError, Source
from sec_research.ingestion.acquisition import Acquisition
from sec_research.ingestion.cli import main
from sec_research.settings import Settings
from tests.sec_helpers import Clock, FakeTransport, client

pytestmark = pytest.mark.integration
FIXTURES = Path(__file__).parents[1] / "fixtures" / "sec"
SOURCE = Source(
    kind="submissions", cik="1", url="https://data.sec.gov/submissions/CIK0000000001.json"
)


def migrate() -> None:
    command.upgrade(Config(str(Path(__file__).parents[2] / "alembic.ini")), "head")


def test_manifest_durable_rerun_versions_and_append_only_history(
    database_settings: Settings,
    tmp_path: Path,
) -> None:
    migrate()
    engine = create_database_engine(database_settings)
    manifest = PostgresManifest(engine)
    run_id = uuid4()
    manifest.begin_run(run_id, {"synthetic": True})
    body = (FIXTURES / "submissions.json").read_bytes()
    transport = FakeTransport(
        Response(200, body, {"content-type": "application/json"}),
        Response(200, body, {"content-type": "application/json"}),
    )
    acquire = Acquisition(client(transport, Clock()), LocalBronze(tmp_path), manifest, run_id)
    try:
        assert acquire.get(SOURCE) == body
        # Recreate the repository/service to exercise persistence rather than an in-memory cache.
        resumed = Acquisition(
            client(transport, Clock()), LocalBronze(tmp_path), PostgresManifest(engine), run_id
        )
        assert resumed.get(SOURCE) == body
        assert len(transport.requests) == 1
        resumed.refresh = True
        resumed.get(SOURCE)
        assert resumed.reconcile() == {"fetches": 2, "objects": 1, "orphans": 0}
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT attempts FROM ingestion_sources")).scalar_one() == 2
            )
            assert (
                connection.execute(text("SELECT count(*) FROM ingestion_attempts")).scalar_one()
                == 4
            )
        with pytest.raises(DBAPIError), engine.begin() as connection:
            connection.execute(text("DELETE FROM ingestion_fetches"))
        with pytest.raises(DBAPIError), engine.begin() as connection:
            connection.execute(text("UPDATE ingestion_attempts SET status='forged'"))
        manifest.finish_run(run_id, failed=False)
        with pytest.raises(DBAPIError):
            command.downgrade(Config(str(Path(__file__).parents[2] / "alembic.ini")), "base")
        assert len(manifest.all_fetches()) == 2
    finally:
        engine.dispose()


def test_work_claim_exclusion_and_release(database_settings: Settings) -> None:
    migrate()
    engine = create_database_engine(database_settings)
    first, second = PostgresManifest(engine), PostgresManifest(engine)
    try:
        with first.claim(SOURCE), pytest.raises(IngestionError, match="busy"), second.claim(SOURCE):
            pytest.fail("a duplicate worker acquired an active source")
        with second.claim(SOURCE):
            pass
    finally:
        engine.dispose()


def test_aggregate_rate_limit_and_deadline(database_settings: Settings) -> None:
    migrate()
    engine = create_database_engine(database_settings)
    try:
        first, second = PostgresLimiter(engine), PostgresLimiter(engine)
        first.wait(time.monotonic() + 5)
        started = time.monotonic()
        second.wait(time.monotonic() + 5)
        assert time.monotonic() - started >= 0.15
        with pytest.raises(IngestionError, match="deadline"):
            first.wait(time.monotonic() + 0.01)
        with engine.begin() as connection:
            connection.execute(text("SELECT pg_advisory_xact_lock(2702001)"))
            with pytest.raises(IngestionError, match="deadline"):
                second.wait(time.monotonic() + 0.05)
    finally:
        engine.dispose()


def test_interrupted_persistent_work_resumes_and_records_failure(
    database_settings: Settings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migrate()
    engine = create_database_engine(database_settings)
    manifest = PostgresManifest(engine)
    run_id = uuid4()
    manifest.begin_run(run_id, {"synthetic": True})
    response = Response(
        200, (FIXTURES / "submissions.json").read_bytes(), {"content-type": "application/json"}
    )
    acquire = Acquisition(
        client(FakeTransport(response), Clock()), LocalBronze(tmp_path), manifest, run_id
    )

    def crash(fetch: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(manifest, "complete", crash)
    try:
        with pytest.raises(KeyboardInterrupt):
            acquire.get(SOURCE)
        with engine.connect() as connection:
            assert (
                connection.execute(text("SELECT status FROM ingestion_sources")).scalar_one()
                == "downloading"
            )
        second_id = uuid4()
        resumed_manifest = PostgresManifest(engine)
        resumed_manifest.begin_run(second_id, {"resume": True})
        transport = FakeTransport(Response(403, b"", {}), response)
        resumed = Acquisition(
            client(transport, Clock()), LocalBronze(tmp_path), resumed_manifest, second_id
        )
        with pytest.raises(IngestionError, match="access_denied"):
            resumed.get(SOURCE)
        assert resumed.get(SOURCE) == response.body
        assert resumed.reconcile() == {"fetches": 1, "objects": 1, "orphans": 0}
        with engine.connect() as connection:
            statuses = (
                connection.execute(text("SELECT status FROM ingestion_attempts ORDER BY id"))
                .scalars()
                .all()
            )
            assert statuses == ["started", "started", "failed", "started", "succeeded"]
        resumed_manifest.finish_run(second_id, failed=False)
    finally:
        engine.dispose()


def test_documented_cli_with_mocked_sec_and_real_database(
    database_settings: Settings,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    migrate()
    calls: list[str] = []

    class Router:
        def __call__(
            self, url: str, headers: Mapping[str, str], timeout: float, max_bytes: int
        ) -> Response:
            calls.append(url)
            if "companyfacts" in url:
                name = "company_facts.json"
            elif "-submissions-" in url:
                name = "history.json"
            elif "submissions" in url:
                name = "submissions.json"
            else:
                name = "filing.htm"
            return Response(
                200,
                (FIXTURES / name).read_bytes(),
                {"content-type": "text/html" if name.endswith("htm") else "application/json"},
            )

    def mock_client(policy: object, *, limiter: object) -> object:
        from sec_research.adapters.sec.client import LocalLimiter, SecClient, SecPolicy

        clock = Clock()
        return SecClient(
            SecPolicy(user_agent="Synthetic contact@example.test"),
            transport=Router(),
            limiter=LocalLimiter(clock=clock.now, sleep=clock.sleep),
            clock=clock.now,
        )

    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setenv("SEC_USER_AGENT", "Synthetic contact@example.test")
    monkeypatch.setattr("sec_research.ingestion.cli.SecClient", mock_client)
    args = ["ingest", "--company", "1", "--max-filings", "2", "--from-date", "2025-01-01"]
    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["filings"] == 2 and first["company_facts"] == 1 and not first["errors"]
    assert len(calls) == 5
    assert main(args) == 0
    assert len(calls) == 5
    capsys.readouterr()
    assert main(["reconcile"]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary == {"fetches": 5, "objects": 4, "orphans": 0}
