"""Explicit Phase 2 -> canonical contract boundary; no I/O or transformations."""

import hashlib

from sec_research.contracts.canonical import SourceReference
from sec_research.ingestion.ports import Fetch


def validated_source(fetch: Fetch, body: bytes) -> SourceReference:
    """Caller reads via the existing Bronze port. Reject quarantined or mismatched bytes."""
    fetch = Fetch.model_validate(fetch.model_dump())
    if fetch.processing_status != "unprocessed":
        raise ValueError("quarantined Bronze input is not eligible")
    if len(body) != fetch.byte_count or hashlib.sha256(body).hexdigest() != fetch.sha256:
        raise ValueError("Bronze source integrity mismatch")
    if fetch.fetched_at.tzinfo is None or fetch.fetched_at.utcoffset() is None:
        raise ValueError("Bronze fetch timestamp requires an explicit timezone")
    return SourceReference(source=fetch.source, sha256=fetch.sha256, byte_count=fetch.byte_count)
