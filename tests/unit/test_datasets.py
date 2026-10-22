from pathlib import Path

import pytest

from sec_research.adapters.storage.parquet import MODELS, LocalDatasets, arrow_schema
from sec_research.contracts.canonical import ContentBlock, FinancialFact, Record
from sec_research.contracts.datasets import DatasetError, SelectionEvidence, SourceOccurrence
from sec_research.processing.dataset_rows import Rows, gold_rows, validate_silver
from sec_research.processing.datasets import (
    build_snapshot,
    load_snapshot,
    partition,
    record_counts,
    verify_snapshot,
)
from tests.dataset_helpers import built_dataset, dataset_inputs


def test_full_roundtrip_replay_and_abstentions(tmp_path: Path) -> None:
    bronze, store, fetches, spec = dataset_inputs(tmp_path)
    first = build_snapshot(bronze, store, fetches, spec)
    second = build_snapshot(bronze, store, list(reversed(fetches)), spec)
    assert first == second
    assert first.id is not None and load_snapshot(store, first.id) == first
    counts = record_counts(first)
    assert counts["silver_xbrl_facts"] == 3
    assert counts["silver_xbrl_occurrences"] == 4
    assert counts["gold_reported_facts"] == 3
    assert counts["gold_research_evidence"] == counts["silver_content_blocks"]
    results = [
        r.result
        for i in first.gold.objects
        if i.dataset == "gold_selections"
        for r in store.read(i)
        if isinstance(r, SelectionEvidence)
    ]
    assert {r.status for r in results} == {"selected", "unsupported", "unavailable"}
    selected = next(r for r in results if r.status == "selected")
    assert selected.selected[0].value == 42
    assert len(selected.alternatives) == 2  # two source occurrences, one logical reporting
    occurrences = [
        r
        for i in first.silver.objects
        if i.dataset == "silver_xbrl_occurrences"
        for r in store.read(i)
        if isinstance(r, SourceOccurrence)
    ]
    assert sum(r.occurrence.quality == "failed" for r in occurrences) == 1
    assert "wp33_rev_001_through_006_unresolved" in first.limitations


@pytest.mark.parametrize("dataset", MODELS)
def test_empty_dataset_has_explicit_schema(tmp_path: Path, dataset: str) -> None:
    store = LocalDatasets(tmp_path)
    obj = store.write(dataset, "test", [])
    assert store.read(obj) == []
    assert arrow_schema(MODELS[dataset]).field("id").nullable is False


def test_corruption_blocks_verification(tmp_path: Path) -> None:
    store, snapshot = built_dataset(tmp_path)
    item = snapshot.gold.objects[0]
    store.path(item.path).write_bytes(b"damaged")
    with pytest.raises(DatasetError, match="checksum"):
        verify_snapshot(store, snapshot)


def test_partial_write_never_creates_completion_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bronze, store, fetches, spec = dataset_inputs(tmp_path)
    original = store.write
    calls = 0

    def interrupted(dataset: str, key: str, rows: list[Record]) -> object:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("simulated interruption")
        return original(dataset, key, rows)

    with monkeypatch.context() as patch:
        patch.setattr(store, "write", interrupted)
        with pytest.raises(OSError, match="simulated"):
            build_snapshot(bronze, store, fetches, spec)
    assert not list(store.root.glob("snapshots/*.json"))
    recovered = build_snapshot(bronze, store, fetches, spec)
    verify_snapshot(store, recovered)


def test_missing_or_duplicate_input_and_versions_fail(tmp_path: Path) -> None:
    bronze, store, fetches, spec = dataset_inputs(tmp_path)
    with pytest.raises(DatasetError, match="duplicate_fetches"):
        build_snapshot(bronze, store, [*fetches, fetches[0]], spec)
    incompatible = spec.model_copy(update={"code_sha256": "0" * 64})
    with pytest.raises(DatasetError, match="build_environment"):
        build_snapshot(bronze, store, fetches, incompatible)
    (bronze.root / "bronze/manifests" / f"{fetches[0].id.hex}.json").write_bytes(b"{}")
    with pytest.raises(DatasetError, match="bronze_manifest"):
        build_snapshot(bronze, store, fetches, spec)


def test_unknown_sections_and_broken_relationships(tmp_path: Path) -> None:
    store, snapshot = built_dataset(tmp_path)
    source = next(e.source for e in snapshot.source_entries if e.source.source.kind == "filing")
    key = partition(source)
    rows: Rows = {
        i.dataset: store.read(i) for i in snapshot.silver.objects if i.path.split("/")[2] == key
    }
    gold = gold_rows(rows)
    assert any(
        getattr(r, "section_classification", None) == "unclassified"
        for r in gold["gold_research_evidence"]
    )
    block = rows["silver_content_blocks"][0]
    assert isinstance(block, ContentBlock)
    rows["silver_content_blocks"][0] = ContentBlock.model_validate(
        {
            **block.model_dump(exclude={"id"}),
            "document_id": "document:" + "0" * 64,
        }
    )
    with pytest.raises(ValueError, match="ownership"):
        validate_silver(rows, snapshot.spec.versions)


def test_duplicate_ids_and_decimal_precision(tmp_path: Path) -> None:
    store, snapshot = built_dataset(tmp_path)
    obj = next(i for i in snapshot.silver.objects if i.dataset == "silver_xbrl_facts")
    fact = store.read(obj)[0]
    assert isinstance(fact, FinancialFact)
    value = "1234567890123456789012345678901234567890.00000000000000000000001"
    precise = FinancialFact.model_validate(
        {
            **fact.model_dump(exclude={"id", "value", "raw_value"}),
            "value": value,
            "raw_value": value,
        }
    )
    written = store.write("silver_xbrl_facts", "precision", [precise])
    assert store.read(written) == [precise]
    with pytest.raises(DatasetError, match="duplicate_record_id"):
        store.write("silver_xbrl_facts", "duplicates", [fact, fact])


@pytest.mark.parametrize("path", ["../bad", "x/../../y", "/absolute", "C:/escape", "x\\y"])
def test_derived_paths_cannot_escape(tmp_path: Path, path: str) -> None:
    with pytest.raises(DatasetError, match="unsafe_dataset_path"):
        LocalDatasets(tmp_path).put(path, b"test")
