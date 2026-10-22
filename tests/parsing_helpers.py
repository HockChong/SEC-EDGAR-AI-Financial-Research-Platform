"""Synthetic Bronze inputs reuse WP3.1 source metadata, never real company labels."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sec_research.ingestion.ports import Fetch

FIXTURES = Path(__file__).parent / "fixtures" / "canonical"


def input_html(body: bytes | str | None = None, fixture: str = "annual.htm") -> tuple[Fetch, bytes]:
    entries = json.loads((FIXTURES / "manifest.json").read_bytes())["fixtures"]
    entry = next(e for e in entries if e["path"] == fixture)
    if body is None:
        body = (FIXTURES / fixture).read_bytes()
    if isinstance(body, str):
        body = body.encode()
    return Fetch(
        id=UUID(int=1),
        run_id=UUID(int=2),
        source=entry["source"],
        sha256=hashlib.sha256(body).hexdigest(),
        storage_uri="file:///synthetic/source",
        manifest_uri="file:///synthetic/manifest",
        fetched_at=datetime(2026, 10, 20, tzinfo=UTC),
        byte_count=len(body),
        http_status=200,
        media_type="text/html",
        attempts=1,
    ), body
