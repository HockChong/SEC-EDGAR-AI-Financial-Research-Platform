"""Synthetic Company Facts inputs, never financial ground truth."""

import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

from sec_research.contracts.sec import Source
from sec_research.ingestion.ports import Fetch


def input_facts(body: bytes) -> Fetch:
    cik = str(json.loads(body)["cik"]).zfill(10)
    return Fetch(
        id=UUID(int=1),
        run_id=UUID(int=2),
        source=Source(
            kind="company_facts",
            cik=cik,
            url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
        ),
        sha256=hashlib.sha256(body).hexdigest(),
        byte_count=len(body),
        storage_uri="file:///synthetic/source",
        manifest_uri="file:///synthetic/manifest",
        fetched_at=datetime(2026, 10, 21, tzinfo=UTC),
        http_status=200,
        media_type="application/json",
        attempts=1,
    )


def body_for(
    rows: list[dict[str, object]],
    concept: str = "NetIncomeLoss",
    unit: str = "USD",
    taxonomy: str = "us-gaap",
) -> bytes:
    return json.dumps(
        {
            "cik": 1,
            "entityName": "Synthetic Example",
            "facts": {taxonomy: {concept: {"units": {unit: rows}}}},
        }
    ).encode()


def raw_fact(**updates: object) -> dict[str, object]:
    return {
        "val": 42,
        "start": "2024-01-01",
        "end": "2024-12-31",
        "accn": "0000000001-25-000001",
        "filed": "2025-02-01",
        "form": "10-K",
        "fy": 2024,
        "fp": "FY",
        **updates,
    }
