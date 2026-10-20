"""Restart-safe acquisition: bytes, immutable manifest, then transactional work completion."""

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Literal, cast
from uuid import UUID, uuid4

from sec_research.adapters.sec.client import SecClient
from sec_research.contracts.sec import IngestionCode, IngestionError, Source
from sec_research.ingestion.payloads import validate_payload
from sec_research.ingestion.ports import Bronze, Fetch, Manifest
from sec_research.observability.logging import Event

logger = logging.getLogger(__name__)


class Acquisition:
    def __init__(
        self,
        client: SecClient,
        store: Bronze,
        manifest: Manifest,
        run_id: UUID,
        *,
        refresh: bool = False,
        max_age: timedelta = timedelta(hours=24),
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if max_age.total_seconds() < 0:
            raise ValueError("max age cannot be negative")
        self.client, self.store, self.manifest, self.run_id = client, store, manifest, run_id
        self.refresh, self.max_age, self.now = refresh, max_age, now

    def get(self, source: Source) -> bytes:
        with self.manifest.claim(source):
            previous = self.manifest.latest(source)
            cached: bytes | None = None
            if previous is not None:
                # Never reuse a success record without verifying the stored bytes.
                try:
                    cached = self.store.read(previous.sha256)
                except IngestionError as failure:
                    self.manifest.start(source, self.run_id)
                    self.manifest.fail(source, self.run_id, failure)
                    raise
                if previous.source != source:
                    raise IngestionError(IngestionCode.INVALID_METADATA)
                if not self.refresh and (
                    source.kind == "filing" or self.now() - previous.fetched_at < self.max_age
                ):
                    return cached
            self.manifest.start(source, self.run_id)
            try:
                validators: dict[str, str] = {}
                if previous is not None:
                    if previous.etag:
                        validators["If-None-Match"] = previous.etag
                    if previous.last_modified:
                        validators["If-Modified-Since"] = previous.last_modified
                response = self.client.get(source.url, validators)
                if response.status == 304:
                    if previous is None or cached is None:
                        raise IngestionError(IngestionCode.INVALID_METADATA)
                    body, media_type = cached, previous.media_type
                else:
                    body = response.body
                    media_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                revalidated = previous if response.status == 304 else None
                sha256, uri = self.store.put(body)
                error: IngestionError | None = None
                try:
                    validate_payload(source, body, media_type)
                except IngestionError as invalid:
                    error = invalid
                fetch = Fetch(
                    id=uuid4(),
                    run_id=self.run_id,
                    source=source,
                    sha256=sha256,
                    storage_uri=uri,
                    manifest_uri="",
                    fetched_at=self.now(),
                    byte_count=len(body),
                    http_status=cast(Literal[200, 304], response.status),
                    media_type=media_type,
                    attempts=response.attempts,
                    etag=response.headers.get("etag", revalidated.etag if revalidated else None),
                    last_modified=response.headers.get(
                        "last-modified", revalidated.last_modified if revalidated else None
                    ),
                    processing_status="quarantined" if error else "unprocessed",
                )
                # Self URI is omitted from the immutable on-disk manifest.
                manifest_uri = self.store.put_manifest(
                    fetch.id.hex, fetch.model_dump_json(exclude={"manifest_uri"}).encode()
                )
                fetch = fetch.model_copy(update={"manifest_uri": manifest_uri})
                self.manifest.complete(fetch)
                if error:
                    error.attempts = response.attempts
                    raise error
                logger.info("Acquired source", extra={"event": Event.INGESTION_SUCCEEDED})
                return body
            except IngestionError as failure:
                self.manifest.fail(source, self.run_id, failure)
                logger.warning("Acquisition failed", extra={"event": Event.INGESTION_FAILED})
                raise

    def reconcile(self) -> dict[str, int]:
        return reconcile(self.store, self.manifest)


def reconcile(store: Bronze, manifest: Manifest) -> dict[str, int]:
    fetches = manifest.all_fetches()
    known = {fetch.sha256 for fetch in fetches}
    for fetch in fetches:
        body = store.read(fetch.sha256)
        expected = fetch.model_dump_json(exclude={"manifest_uri"}).encode()
        if len(body) != fetch.byte_count or store.read_manifest(fetch.id.hex) != expected:
            raise IngestionError(IngestionCode.INTEGRITY)
    checksums = store.checksums()
    for checksum in checksums:
        store.read(checksum)
    return {
        "fetches": len(fetches),
        "objects": len(checksums),
        "orphans": len(set(checksums) - known),
    }
