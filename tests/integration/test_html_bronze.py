"""Offline integration of real immutable storage, manifests, parser and diagnostics."""

import json
from pathlib import Path

import pytest

from sec_research.adapters.storage.local import LocalBronze
from sec_research.contracts.parsing import ParsedDocument, ParseFailure
from sec_research.ingestion.ports import Fetch
from sec_research.processing.corpus import audit_bronze, main
from sec_research.processing.html import parse_batch
from tests.parsing_helpers import input_html


def publish(store: LocalBronze, fixture: str = "annual.htm", body: str | None = None) -> Fetch:
    fetch, data = input_html(body, fixture=fixture)
    sha, uri = store.put(data)
    fetch = fetch.model_copy(update={"storage_uri": uri})
    manifest_uri = store.put_manifest(
        fetch.id.hex, fetch.model_dump_json(exclude={"manifest_uri"}).encode()
    )
    assert sha == fetch.sha256
    return fetch.model_copy(update={"manifest_uri": manifest_uri})


def test_manifest_source_parser_roundtrip(tmp_path: Path) -> None:
    store = LocalBronze(tmp_path / "artifacts")
    fetch = publish(store)
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps({"fetches": [fetch.model_dump(mode="json")]}))
    audited = audit_bronze(store, inventory)
    parsed = list(parse_batch((f, store.read(f.sha256)) for f in audited))
    assert len(parsed) == 1 and isinstance(parsed[0], ParsedDocument)
    assert parsed[0].document.source.sha256 == fetch.sha256
    assert (
        store.read_manifest(fetch.id.hex)
        == fetch.model_dump_json(exclude={"manifest_uri"}).encode()
    )


def test_bad_document_does_not_discard_neighboring_results() -> None:
    good = input_html()
    bad = input_html("<script>no content</script>")
    results = list(parse_batch([good, bad, good]))
    assert len(results) == 3
    assert isinstance(results[0], ParsedDocument)
    assert isinstance(results[1], ParseFailure)
    assert results[1].code == "no_visible_content"
    assert results[0] == results[2]


@pytest.mark.parametrize("corrupt", ["inventory", "manifest", "orphan", "missing"])
def test_audit_rejects_untrusted_inventory_and_manifest(tmp_path: Path, corrupt: str) -> None:
    store = LocalBronze(tmp_path / "artifacts")
    fetch = publish(store)
    data = fetch.model_dump(mode="json")
    if corrupt == "inventory":
        data["byte_count"] = 1
    elif corrupt == "manifest":
        (store.root / "bronze/manifests" / f"{fetch.id.hex}.json").write_bytes(b"{}")
    elif corrupt == "orphan":
        store.put(b"orphan")
    else:
        store.path(fetch.sha256).unlink()
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps({"fetches": [data]}))
    # Missing objects are reported by the existing structured Bronze error.
    from sec_research.contracts.sec import IngestionError

    with pytest.raises((ValueError, IngestionError)):
        audit_bronze(store, inventory)


@pytest.mark.parametrize("body,status", [(None, 0), ("<script>no visible content</script>", 1)])
def test_offline_diagnostic_command(tmp_path: Path, body: str | None, status: int) -> None:
    store = LocalBronze(tmp_path / "artifacts")
    fetch = publish(store, body=body)
    filing = fetch.source.filing
    assert filing is not None
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps({"fetches": [fetch.model_dump(mode="json")]}))
    split = tmp_path / "split.json"
    split.write_text(
        json.dumps(
            {
                "schema_version": "wp32-split-1",
                "frozen_before_heuristic_development": True,
                "policy": "Synthetic command integration test",
                "filings": [
                    {
                        "cik": filing.cik,
                        "form": filing.form,
                        "accession": filing.accession,
                        "source_sha256": fetch.sha256,
                        "split": "development",
                    }
                ],
            }
        )
    )
    benchmark = tmp_path / "labels.json"
    benchmark.write_text(
        json.dumps(
            {
                "schema_version": "wp32-boundaries-1",
                "annotation_method": "Synthetic, unlabeled",
                "human_adjudicated": False,
                "cases": [],
            }
        )
    )
    output = tmp_path / "result.json"
    assert (
        main(
            [
                "--artifact-root",
                str(store.root),
                "--inventory",
                str(inventory),
                "--split-file",
                str(split),
                "--benchmark",
                str(benchmark),
                "--output",
                str(output),
            ]
        )
        == status
    )
    report = json.loads(output.read_bytes())
    assert report["bronze_fetches_verified"] == 1
    assert report["metrics"]["all"]["parsed" if status == 0 else "failed"] == 1
