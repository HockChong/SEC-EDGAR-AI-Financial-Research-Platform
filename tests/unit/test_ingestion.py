import hashlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from sec_research.adapters.sec.client import Response
from sec_research.adapters.storage.local import LocalBronze
from sec_research.contracts.sec import IngestionCode, IngestionError, Source
from sec_research.ingestion.acquisition import Acquisition
from sec_research.ingestion.cli import ingest_companies, parser
from sec_research.ingestion.companies import resolve_company
from sec_research.ingestion.company_facts import ingest_company_facts
from sec_research.ingestion.filings import discover_filings
from sec_research.ingestion.payloads import json_object
from sec_research.ingestion.ports import Fetch
from tests.sec_helpers import Clock, FakeTransport, client

FIXTURES = Path(__file__).parents[1] / "fixtures" / "sec"
SUBMISSIONS = Source(
    kind="submissions", cik="1", url="https://data.sec.gov/submissions/CIK0000000001.json"
)


def response(name: str) -> Response:
    return Response(
        200,
        (FIXTURES / name).read_bytes(),
        {
            "content-type": "text/html" if name.endswith("htm") else "application/json",
            "etag": '"synthetic-v1"',
        },
    )


class MemoryManifest:
    def __init__(self) -> None:
        self.fetches: list[Fetch] = []
        self.states: dict[str, str] = {}
        self.errors: list[IngestionError] = []

    @contextmanager
    def claim(self, source: Source) -> Iterator[None]:
        yield

    def latest(self, source: Source) -> Fetch | None:
        return next(
            (
                item
                for item in reversed(self.fetches)
                if item.source == source and item.processing_status == "unprocessed"
            ),
            None,
        )

    def start(self, source: Source, run_id: UUID) -> None:
        self.states[source.url] = "downloading"

    def complete(self, fetch: Fetch) -> None:
        self.fetches.append(fetch)
        self.states[fetch.source.url] = "succeeded"

    def fail(self, source: Source, run_id: UUID, error: IngestionError) -> None:
        self.states[source.url] = "failed"
        self.errors.append(error)

    def all_fetches(self) -> list[Fetch]:
        return self.fetches


def acquisition(
    tmp_path: Path, *responses: Response | Exception
) -> tuple[Acquisition, MemoryManifest, FakeTransport]:
    manifest = MemoryManifest()
    transport = FakeTransport(*responses)
    acquire = Acquisition(client(transport, Clock()), LocalBronze(tmp_path), manifest, uuid4())
    return acquire, manifest, transport


def test_discovery_traverses_history_filters_amendments_and_reuses_sources(tmp_path: Path) -> None:
    acquire, manifest, transport = acquisition(
        tmp_path, response("submissions.json"), response("history.json")
    )
    filings = discover_filings(acquire, "1")
    assert [filing.form for filing in filings] == ["10-K", "10-Q"]
    assert filings[0].source_url.endswith("/1/000000000126000001/annual.htm")
    assert len(discover_filings(acquire, "1", include_amendments=True)) == 3
    assert len(discover_filings(acquire, "1", max_filings=1)) == 1
    assert [
        filing.form
        for filing in discover_filings(acquire, "1", start=date(2025, 1, 1), end=date(2025, 12, 31))
    ] == ["10-Q"]
    assert len(transport.requests) == 2
    assert len(manifest.fetches) == 2


def test_history_date_ranges_avoid_unnecessary_downloads(tmp_path: Path) -> None:
    acquire, _, transport = acquisition(tmp_path, response("submissions.json"))
    assert len(discover_filings(acquire, "1", start=date(2026, 1, 1))) == 1
    assert len(transport.requests) == 1


def test_exact_company_lookup_and_ambiguity(tmp_path: Path) -> None:
    acquire, _, transport = acquisition(tmp_path, response("companies.json"))
    assert resolve_company("synth", acquire) == "0000000001"
    assert resolve_company("Synthetic Test Company", acquire) == "0000000001"
    assert resolve_company("1", acquire) == "0000000001"
    with pytest.raises(IngestionError):
        resolve_company("missing", acquire)
    assert len(transport.requests) == 1


def test_identical_and_changed_json_versions_preserve_originals(tmp_path: Path) -> None:
    original = response("company_facts.json")
    changed = Response(
        200,
        original.body.replace(b"123456789.123456789", b"9.123456789"),
        {"content-type": "application/json"},
    )
    acquire, manifest, transport = acquisition(tmp_path, original, original, changed)
    assert ingest_company_facts(acquire, "1") == original.body
    assert ingest_company_facts(acquire, "1") == original.body
    assert len(transport.requests) == 1
    acquire.refresh = True
    ingest_company_facts(acquire, "1")
    ingest_company_facts(acquire, "1")
    assert len(manifest.fetches) == 3
    assert manifest.fetches[0].sha256 == manifest.fetches[1].sha256
    assert manifest.fetches[0].sha256 != manifest.fetches[2].sha256
    assert acquire.store.read(manifest.fetches[0].sha256) == original.body
    assert acquire.reconcile() == {"fetches": 3, "objects": 2, "orphans": 0}


def test_conditional_revalidation_and_unexpected_304(tmp_path: Path) -> None:
    acquire, manifest, transport = acquisition(
        tmp_path, response("submissions.json"), Response(304, b"", {})
    )
    original = acquire.get(SUBMISSIONS)
    acquire.refresh = True
    assert acquire.get(SUBMISSIONS) == original
    assert manifest.fetches[-1].http_status == 304
    assert transport.requests[-1][1]["If-None-Match"] == '"synthetic-v1"'
    acquire, manifest, _ = acquisition(tmp_path / "unexpected", Response(304, b"", {}))
    with pytest.raises(IngestionError, match="invalid_metadata"):
        acquire.get(SUBMISSIONS)
    assert not manifest.fetches


@pytest.mark.parametrize(
    "body", [b"not-json", b'{"cik":1,"cik":2}', b'{"cik":NaN}', b'{"cik":2}', b"[]", b"\xff"]
)
def test_invalid_metadata_is_preserved_quarantined_and_never_cached(
    tmp_path: Path, body: bytes
) -> None:
    acquire, manifest, _ = acquisition(
        tmp_path, Response(200, body, {"content-type": "application/json"})
    )
    with pytest.raises(IngestionError):
        acquire.get(SUBMISSIONS)
    assert manifest.fetches[0].processing_status == "quarantined"
    assert acquire.store.read(hashlib.sha256(body).hexdigest()) == body
    assert manifest.states[SUBMISSIONS.url] == "failed"
    assert manifest.latest(SUBMISSIONS) is None


def test_interrupted_commit_leaves_orphan_and_can_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    acquire, manifest, _ = acquisition(
        tmp_path, response("submissions.json"), response("submissions.json")
    )
    complete = manifest.complete

    def interrupted(fetch: Fetch) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(manifest, "complete", interrupted)
    with pytest.raises(KeyboardInterrupt):
        acquire.get(SUBMISSIONS)
    assert manifest.states[SUBMISSIONS.url] == "downloading"
    assert acquire.reconcile()["orphans"] == 1
    monkeypatch.setattr(manifest, "complete", complete)
    acquire.get(SUBMISSIONS)
    assert acquire.reconcile() == {"fetches": 1, "objects": 1, "orphans": 0}


def test_integrity_corruption_blocks_reuse_and_reconcile(tmp_path: Path) -> None:
    acquire, manifest, transport = acquisition(tmp_path, response("submissions.json"))
    acquire.get(SUBMISSIONS)
    store = LocalBronze(tmp_path)
    store.path(manifest.fetches[0].sha256).write_bytes(b"corrupted")
    with pytest.raises(IngestionError, match="integrity"):
        acquire.get(SUBMISSIONS)
    with pytest.raises(IngestionError, match="integrity"):
        acquire.reconcile()
    assert len(transport.requests) == 1


def test_storage_create_only_collision_partial_write_and_disk_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = LocalBronze(tmp_path)
    checksum, _ = store.put(b"original")
    store.put(b"original")
    store.path(checksum).write_bytes(b"corrupt")
    with pytest.raises(IngestionError, match="integrity"):
        store.put(b"original")

    def fail_link(source: str, target: Path) -> None:
        raise OSError("private disk details")

    monkeypatch.setattr("sec_research.adapters.storage.local.os.link", fail_link)
    with pytest.raises(IngestionError, match="storage"):
        store.put(b"new object")
    assert not list(tmp_path.rglob(".stage-*"))
    assert len(store.checksums()) == 1


def test_bad_column_lengths_and_unsafe_primary_document(tmp_path: Path) -> None:
    raw = json_object(response("submissions.json").body)
    for primary in [[], ["../private.htm", "event.htm"]]:
        data = json.loads(json.dumps(raw))
        data["filings"]["recent"]["primaryDocument"] = primary
        acquire, _, _ = acquisition(
            tmp_path / str(len(primary)),
            Response(200, json.dumps(data).encode(), {"content-type": "application/json"}),
        )
        with pytest.raises(IngestionError):
            discover_filings(acquire, "1")


def test_manifest_tampering_is_detected(tmp_path: Path) -> None:
    acquire, manifest, _ = acquisition(tmp_path, response("submissions.json"))
    acquire.get(SUBMISSIONS)
    path = tmp_path / "bronze" / "manifests" / f"{manifest.fetches[0].id.hex}.json"
    path.write_text("{}")
    with pytest.raises(IngestionError, match="integrity"):
        acquire.reconcile()


def test_invalid_history_url_and_conflicting_duplicate_accession(tmp_path: Path) -> None:
    raw = json.loads(response("submissions.json").body)
    raw["filings"]["files"][0]["name"] = "../../private.json"
    acquire, _, _ = acquisition(
        tmp_path, Response(200, json.dumps(raw).encode(), {"content-type": "application/json"})
    )
    with pytest.raises(IngestionError):
        discover_filings(acquire, "1")
    history = json.loads(response("history.json").body)
    history["accessionNumber"][0] = "0000000001-26-000001"
    acquire, _, _ = acquisition(
        tmp_path / "conflict",
        response("submissions.json"),
        Response(200, json.dumps(history).encode(), {"content-type": "application/json"}),
    )
    with pytest.raises(IngestionError):
        discover_filings(acquire, "1")


def test_expired_json_refreshes_and_filing_stays_immutable(tmp_path: Path) -> None:
    acquire, _, transport = acquisition(
        tmp_path, response("submissions.json"), response("submissions.json")
    )
    acquire.now = lambda: datetime(2025, 1, 1, tzinfo=UTC)
    acquire.get(SUBMISSIONS)
    acquire.now = lambda: datetime(2025, 1, 3, tzinfo=UTC)
    acquire.get(SUBMISSIONS)
    assert len(transport.requests) == 2
    assert IngestionCode.INTEGRITY.value == "integrity"


def test_partial_filing_failure_resumes_only_missing_download(tmp_path: Path) -> None:
    acquire, manifest, transport = acquisition(
        tmp_path,
        response("submissions.json"),
        response("history.json"),
        Response(404, b"", {}),
        response("filing.htm"),
        response("company_facts.json"),
        response("filing.htm"),
    )
    args = parser().parse_args(["ingest", "--company", "1"])
    summary = ingest_companies(acquire, args)
    assert summary == {"companies": 1, "filings": 1, "company_facts": 1, "errors": ["http_failure"]}
    assert ingest_companies(acquire, args) == {
        "companies": 1,
        "filings": 2,
        "company_facts": 1,
        "errors": [],
    }
    assert len(transport.requests) == 6
    assert len(manifest.fetches) == 5


def test_access_denied_stops_entire_run(tmp_path: Path) -> None:
    acquire, _, transport = acquisition(
        tmp_path, response("submissions.json"), response("history.json"), Response(403, b"", {})
    )
    args = parser().parse_args(["ingest", "--company", "1", "--company", "2"])
    assert ingest_companies(acquire, args)["errors"] == ["access_denied"]
    assert len(transport.requests) == 3


@pytest.mark.parametrize(
    "arguments",
    [
        ["--max-companies", "1", "--company", "2"],
        ["--from-date", "2026-01-01", "--to-date", "2025-01-01"],
        ["--max-age-hours", "nan"],
    ],
)
def test_invalid_run_bounds_make_no_requests(tmp_path: Path, arguments: list[str]) -> None:
    acquire, _, transport = acquisition(tmp_path)
    args = parser().parse_args(["ingest", "--company", "1", *arguments])
    with pytest.raises(IngestionError):
        ingest_companies(acquire, args)
    assert not transport.requests


def test_duplicate_cik_aliases_do_not_repeat_ingestion(tmp_path: Path) -> None:
    acquire, _, transport = acquisition(
        tmp_path,
        response("submissions.json"),
        response("history.json"),
        response("filing.htm"),
        response("filing.htm"),
        response("company_facts.json"),
    )
    args = parser().parse_args(["ingest", "--company", "1", "--company", "0000000001"])
    assert ingest_companies(acquire, args)["companies"] == 1
    assert len(transport.requests) == 5


def test_source_contract_rejects_identity_mismatch() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Source(
            kind="company_facts",
            cik="2",
            url="https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json",
        )


def test_incomplete_fsync_never_publishes_bronze(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = LocalBronze(tmp_path)

    def disk_full(descriptor: int) -> None:
        raise OSError("synthetic disk full")

    monkeypatch.setattr("sec_research.adapters.storage.local.os.fsync", disk_full)
    with pytest.raises(IngestionError, match="storage"):
        store.put(b"incomplete")
    assert not store.checksums()
    assert not list(tmp_path.rglob(".stage-*"))


def test_filing_availability_dates_remain_distinct(tmp_path: Path) -> None:
    data = json.loads(response("submissions.json").body)
    data["filings"]["recent"]["reportDate"] = ["2025-12-31", ""]
    data["filings"]["recent"]["acceptanceDateTime"] = ["2026-02-01T10:00:00Z", ""]
    acquire, _, _ = acquisition(
        tmp_path, Response(200, json.dumps(data).encode(), {"content-type": "application/json"})
    )
    filing = discover_filings(acquire, "1", start=date(2026, 1, 1))[0]
    assert filing.report_date == date(2025, 12, 31)
    assert filing.filing_date == date(2026, 2, 1)
    assert filing.accepted_at == datetime(2026, 2, 1, 10, tzinfo=UTC)
