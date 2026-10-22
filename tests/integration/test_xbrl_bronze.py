"""Real LocalBronze + Company Facts CLI integration, offline and database-free."""

import json
from pathlib import Path

import pytest

from sec_research.adapters.storage.local import LocalBronze
from sec_research.contracts.xbrl import NormalizedFacts
from sec_research.processing.xbrl_corpus import main
from tests.xbrl_helpers import body_for, input_facts, raw_fact


def test_bronze_cli_replay_and_write_boundary(tmp_path: Path) -> None:
    body = body_for([raw_fact(), raw_fact(val=-3)])
    store = LocalBronze(tmp_path / "artifacts")
    sha, uri = store.put(body)
    fetch = input_facts(body).model_copy(update={"storage_uri": uri})
    manifest_uri = store.put_manifest(
        fetch.id.hex, fetch.model_dump_json(exclude={"manifest_uri"}).encode()
    )
    fetch = fetch.model_copy(update={"manifest_uri": manifest_uri})
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps({"fetches": [fetch.model_dump(mode="json")]}))
    output = tmp_path / "audit.json"
    args = [
        "--artifact-root",
        str(store.root),
        "--inventory",
        str(inventory),
        "--as-of",
        "2026-10-21",
        "--output",
        str(output),
    ]
    assert main(args) == 0
    first = output.read_bytes()
    assert main(args) == 0 and output.read_bytes() == first
    report = json.loads(first)
    assert report["rows"][0]["selection_status_counts"]["ambiguous"] == 1
    assert report["rows"][0]["source_pointers_verified"] == 2
    path = tmp_path / "audit-observations" / f"0000000001-{sha}.json"
    assert len(NormalizedFacts.model_validate_json(path.read_bytes()).observations) == 2
    assert store.read(sha) == body
    with pytest.raises(ValueError, match="outside immutable Bronze"):
        main([*args[:-1], str(store.root / "report.json")])
