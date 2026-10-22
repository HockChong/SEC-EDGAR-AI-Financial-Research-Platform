"""Offline table extraction through immutable Bronze and diagnostics CLI."""

import json
from pathlib import Path

import pytest

from sec_research.adapters.storage.local import LocalBronze
from sec_research.processing.table_corpus import main
from tests.integration.test_html_bronze import publish


def test_bronze_table_diagnostics_and_review_candidates(tmp_path: Path) -> None:
    store = LocalBronze(tmp_path / "artifacts")
    fetch = publish(
        store,
        body="""<table><caption>Consolidated balance sheets</caption>
    <tr><th>Metric</th><th>2025</th><th>2024</th></tr>
    <tr><th scope="row">Assets</th><td>20</td><td>10</td></tr></table>""",
    )
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps({"fetches": [fetch.model_dump(mode="json")]}))
    output = tmp_path / "diagnostics.json"
    arguments = ["--artifact-root", str(store.root), "--inventory", str(inventory)]
    assert main([*arguments, "--output", str(output)]) == 0
    report = json.loads(output.read_bytes())
    assert report["counts"]["raw_cells_verified"] == 6
    assert report["counts"]["financial_statement"] == 1
    assert report["rows"][0]["deterministic_replay"] is True
    assert report["bronze_unchanged_after_extraction"] is True
    assert report["normalization_complete"] is True
    assert report["counts"]["normalization_parsed"] == 4
    samples = json.loads(output.with_name("diagnostics-samples.json").read_bytes())
    assert samples["human_adjudicated"] is False
    assert samples["cases"][0]["human_adjudication"] == "pending"
    assert samples["cases"][0]["source_sha256"] == fetch.sha256
    with pytest.raises(ValueError, match="immutable Bronze"):
        main([*arguments, "--output", str(store.root / "bad.json")])
