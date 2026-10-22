"""Small immutable Bronze corpus for dataset and transaction failure tests."""

from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

from sec_research.adapters.storage.local import LocalBronze
from sec_research.adapters.storage.parquet import LocalDatasets
from sec_research.contracts.canonical import ReportingPeriod
from sec_research.contracts.datasets import BuildSpec, Snapshot
from sec_research.contracts.xbrl import SelectionRequest
from sec_research.ingestion.ports import Fetch
from sec_research.processing.datasets import build_snapshot, make_spec
from tests.parsing_helpers import input_html
from tests.xbrl_helpers import body_for, input_facts, raw_fact

RUN_AT = datetime(2026, 10, 22, tzinfo=UTC)


def dataset_inputs(root: Path) -> tuple[LocalBronze, LocalDatasets, list[Fetch], BuildSpec]:
    bronze = LocalBronze(root / "bronze-root")
    store = LocalDatasets(root / "datasets")
    html_fetch, html = input_html(
        "<html><body><p>Unclassified evidence.</p><h1>Item 8. Financial Statements</h1>"
        "<table><caption>Net income</caption><tr><th>2024</th><th>2023</th></tr>"
        "<tr><td>(42)</td><td>13</td></tr></table>"
        '<table><tr><td rowspan="bad">raw quarantine</td></tr></table></body></html>'
    )
    body = body_for(
        [
            raw_fact(),
            raw_fact(),
            raw_fact(val=44, filed="2026-02-01", accn="0000000001-26-000001"),
            raw_fact(end="2025-12-31", filed="2025-02-01"),
        ]
    )
    facts_fetch = input_facts(body).model_copy(update={"id": UUID(int=3)})
    fetches: list[Fetch] = []
    for fetch, content in ((html_fetch, html), (facts_fetch, body)):
        checksum, uri = bronze.put(content)
        fetch = fetch.model_copy(
            update={
                "sha256": checksum,
                "storage_uri": uri,
                "manifest_uri": (
                    bronze.root / "bronze/manifests" / f"{fetch.id.hex}.json"
                ).as_uri(),
            }
        )
        bronze.put_manifest(fetch.id.hex, fetch.model_dump_json(exclude={"manifest_uri"}).encode())
        fetches.append(fetch)
    period = ReportingPeriod(
        kind="duration", start=date(2024, 1, 1), end=date(2024, 12, 31), duration_class="unknown"
    )
    requests = [
        SelectionRequest(cik="0000000001", metric=metric, period=period, as_of=date(2025, 2, 1))
        for metric in ("net_income", "revenue")
    ]
    requests.append(
        SelectionRequest(
            cik="0000000001", metric="net_income", period=period, as_of=date(2024, 12, 31)
        )
    )
    spec = make_spec("synthetic", Path("uv.lock"), RUN_AT, requests)
    return bronze, store, fetches, spec


def built_dataset(root: Path) -> tuple[LocalDatasets, Snapshot]:
    bronze, store, fetches, spec = dataset_inputs(root)
    return store, build_snapshot(bronze, store, fetches, spec)
