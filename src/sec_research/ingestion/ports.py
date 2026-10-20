"""Typed persistence boundary for ingestion orchestration."""

from contextlib import AbstractContextManager
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from pydantic import Field

from sec_research.contracts.sec import Contract, IngestionError, Source


class Fetch(Contract):
    id: UUID
    run_id: UUID
    source: Source
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    storage_uri: str
    manifest_uri: str
    fetched_at: datetime
    byte_count: int = Field(ge=0)
    http_status: Literal[200, 304]
    media_type: str
    etag: str | None = None
    last_modified: str | None = None
    attempts: int = Field(ge=1)
    processing_status: Literal["unprocessed", "quarantined"] = "unprocessed"
    pipeline_version: Literal["bronze-1"] = "bronze-1"


class Manifest(Protocol):
    def claim(self, source: Source) -> AbstractContextManager[None]: ...

    def latest(self, source: Source) -> Fetch | None: ...

    def start(self, source: Source, run_id: UUID) -> None: ...

    def complete(self, fetch: Fetch) -> None: ...

    def fail(self, source: Source, run_id: UUID, error: IngestionError) -> None: ...

    def all_fetches(self) -> list[Fetch]: ...


class Bronze(Protocol):
    def read(self, checksum: str) -> bytes: ...

    def put(self, body: bytes) -> tuple[str, str]: ...

    def put_manifest(self, manifest_id: str, body: bytes) -> str: ...

    def read_manifest(self, manifest_id: str) -> bytes: ...

    def checksums(self) -> list[str]: ...
