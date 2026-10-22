import json
from datetime import timedelta
from pathlib import Path
from uuid import UUID

import pytest

from sec_research.adapters.storage.parquet import LocalDatasets
from sec_research.contracts.canonical import CanonicalFiling, FinancialFact, QualityEvent
from sec_research.contracts.datasets import DatasetError, SourceOccurrence
from sec_research.processing.dataset_cli import main
from sec_research.processing.dataset_rows import (
    Rows,
    html_rows,
    validate_silver,
    xbrl_rows,
)
from sec_research.processing.datasets import build_snapshot, versions
from sec_research.processing.html import parse_html
from sec_research.processing.tables import extract_tables
from sec_research.processing.xbrl import normalize_company_facts
from tests.dataset_helpers import dataset_inputs
from tests.parsing_helpers import input_html
from tests.xbrl_helpers import body_for, input_facts, raw_fact


def test_repeated_fetch_preserves_occurrences_without_duplicate_records(tmp_path: Path) -> None:
    bronze, store, fetches, spec = dataset_inputs(tmp_path)
    extra = fetches[1].model_copy(
        update={
            "id": UUID(int=99),
            "fetched_at": fetches[1].fetched_at + timedelta(hours=1),
        }
    )
    bronze.put_manifest(extra.id.hex, extra.model_dump_json(exclude={"manifest_uri"}).encode())
    snapshot = build_snapshot(bronze, store, [*fetches, extra], spec)
    assert len(snapshot.source_entries) == 3
    assert (
        sum(i.row_count for i in snapshot.silver.objects if i.dataset == "silver_xbrl_facts") == 3
    )
    assert (
        sum(i.row_count for i in snapshot.silver.objects if i.dataset == "silver_provenance") == 3
    )


def test_unsupported_unit_remains_silver_with_reason() -> None:
    body = body_for([raw_fact()], unit="EUR")
    result = normalize_company_facts(input_facts(body), body)
    rows = xbrl_rows(result)
    fact = rows["silver_xbrl_facts"][0]
    assert isinstance(fact, FinancialFact) and fact.unit == "EUR"
    occurrence = rows["silver_xbrl_occurrences"][0]
    assert isinstance(occurrence, SourceOccurrence)
    assert "unsupported_unit" in occurrence.occurrence.reasons


def test_ambiguous_observations_survive_selection(tmp_path: Path) -> None:
    from sec_research.contracts.datasets import SelectionEvidence

    bronze, store, fetches, spec = dataset_inputs(tmp_path)
    body = body_for([raw_fact(), raw_fact(val=99)])
    fetch = fetches[1]
    checksum, uri = bronze.put(body)
    conflicting = fetch.model_copy(
        update={
            "id": UUID(int=100),
            "sha256": checksum,
            "storage_uri": uri,
            "byte_count": len(body),
        }
    )
    bronze.put_manifest(
        conflicting.id.hex, conflicting.model_dump_json(exclude={"manifest_uri"}).encode()
    )
    snapshot = build_snapshot(bronze, store, [fetches[0], conflicting], spec)
    selected = [
        r.result
        for i in snapshot.gold.objects
        if i.dataset == "gold_selections"
        for r in store.read(i)
        if isinstance(r, SelectionEvidence)
    ]
    ambiguous = next(r for r in selected if r.status == "ambiguous")
    assert ambiguous.selected == ()
    assert "conflicting_accession_observations" in ambiguous.reasons


def test_quarantined_table_has_explicit_failed_quality() -> None:
    fetch, body = input_html(
        '<p>Unknown section</p><table><tr><td rowspan="bad">42</td></tr></table>'
    )
    parsed = parse_html(fetch, body)
    tables = extract_tables(fetch, body)
    rows = html_rows(parsed, tables)
    events = [e for e in rows["silver_parse_quality"] if isinstance(e, QualityEvent)]
    assert any(e.state == "failed" and e.disposition == "quarantine" for e in events)
    assert len(rows["silver_table_details"]) == 1 and rows["silver_tables"] == []


@pytest.mark.parametrize(
    "mutation", ["missing_cells", "missing_details", "extra_dataset", "version"]
)
def test_incomplete_or_incompatible_partitions_block(tmp_path: Path, mutation: str) -> None:
    bronze, store, fetches, spec = dataset_inputs(tmp_path)
    snapshot = build_snapshot(bronze, store, fetches, spec)
    items = [i for i in snapshot.silver.objects if i.dataset == "silver_documents"]
    key = items[0].path.split("/")[2]
    rows: Rows = {
        i.dataset: store.read(i) for i in snapshot.silver.objects if i.path.split("/")[2] == key
    }
    if mutation == "missing_cells":
        rows["silver_table_cells"].pop()
    elif mutation == "missing_details":
        rows["silver_table_details"].pop()
    elif mutation == "extra_dataset":
        rows["unexpected"] = []
    else:
        bad = spec.versions.model_copy(update={"parser": "incompatible"})
        with pytest.raises(DatasetError, match="parser_version"):
            validate_silver(rows, bad)
        return
    with pytest.raises((ValueError, DatasetError)):
        validate_silver(rows, versions())


def test_phase2_acceptance_timezone_survives_arrow(tmp_path: Path) -> None:
    fetch, body = input_html()
    filing = parse_html(fetch, body).filing
    content = filing.model_dump(mode="json", exclude={"id"})
    content["filing"]["accepted_at"] = "2026-01-01T12:34:56-05:00"
    content["source"]["source"]["filing"]["accepted_at"] = "2026-01-01T12:34:56-05:00"
    revised = CanonicalFiling.model_validate(content)
    store = LocalDatasets(tmp_path)
    item = store.write("silver_filings", "timezone", [revised])
    assert store.read(item) == [revised]
    assert revised.filing.accepted_at is not None
    assert revised.filing.accepted_at.utcoffset() == timedelta(hours=-5)


def test_integer_overflow_and_immutable_conflict(tmp_path: Path) -> None:
    fetch, body = input_html()
    block = parse_html(fetch, body).blocks[0]
    huge = type(block).model_validate({**block.model_dump(exclude={"id"}), "ordinal": 2**64})
    store = LocalDatasets(tmp_path)
    with pytest.raises(OverflowError):
        store.write("silver_content_blocks", "overflow", [huge])
    store.put("probe.json", b"first")
    store.put("probe.json", b"first")
    with pytest.raises(DatasetError, match="immutable_dataset_conflict"):
        store.put("probe.json", b"second")


def test_overlapping_roots_block_before_writing(tmp_path: Path) -> None:
    bronze, _, fetches, spec = dataset_inputs(tmp_path)
    with pytest.raises(DatasetError, match="overlapping_bronze"):
        build_snapshot(bronze, LocalDatasets(bronze.root / "derived"), fetches, spec)


def test_cli_reports_safe_failure_and_help(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as help_exit:
        main(["--help"])
    assert help_exit.value.code == 0
    assert main(["verify", "--dataset-root", str(tmp_path), "--snapshot-id", "invalid"]) == 1
    assert '"code": "invalid_snapshot_identity"' in capsys.readouterr().out


def test_cli_prepares_builds_and_verifies_pinned_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bronze, store, fetches, spec = dataset_inputs(tmp_path)
    requests = tmp_path / "requests.json"
    requests.write_text(
        json.dumps([r.model_dump(mode="json") for r in spec.requests]), encoding="utf-8"
    )
    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        json.dumps({"fetches": [f.model_dump(mode="json") for f in fetches]}), encoding="utf-8"
    )
    spec_file = tmp_path / "spec.json"
    assert (
        main(
            [
                "prepare",
                "--code-revision",
                "cli-test",
                "--run-at",
                spec.run_at.isoformat(),
                "--requests",
                str(requests),
                "--spec",
                str(spec_file),
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        main(
            [
                "build",
                "--artifact-root",
                str(bronze.root),
                "--inventory",
                str(inventory),
                "--spec",
                str(spec_file),
                "--dataset-root",
                str(store.root),
            ]
        )
        == 0
    )
    snapshot_id = json.loads(capsys.readouterr().out)["snapshot_id"]
    assert (
        main(
            [
                "verify",
                "--dataset-root",
                str(store.root),
                "--snapshot-id",
                snapshot_id,
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["independent_financial_accuracy"] == "not_performed"
