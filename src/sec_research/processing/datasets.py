"""Deterministic Silver/Gold builds and complete-snapshot verification."""

import hashlib
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import pyarrow as pa

from sec_research.adapters.storage.local import LocalBronze
from sec_research.adapters.storage.parquet import LocalDatasets
from sec_research.contracts.bronze import validated_source
from sec_research.contracts.canonical import (
    DatasetObject,
    DatasetPublication,
    FinancialFact,
    Record,
    SourceProvenance,
    SourceReference,
    canonical_bytes,
    stable_id,
)
from sec_research.contracts.datasets import (
    PIPELINE,
    BuildSpec,
    DatasetError,
    ProcessingVersions,
    SelectionEvidence,
    Snapshot,
    SourceEntry,
)
from sec_research.contracts.xbrl import SelectionRequest
from sec_research.domain.financial_selection import select_facts
from sec_research.domain.metrics import METRICS, metric_definition
from sec_research.ingestion.ports import Fetch
from sec_research.processing.dataset_rows import (
    Rows,
    gold_rows,
    html_rows,
    same,
    validate_silver,
    xbrl_rows,
)
from sec_research.processing.dom import PARSER_VERSION
from sec_research.processing.html import parse_html
from sec_research.processing.sections import CLASSIFIER_VERSION
from sec_research.processing.tables import extract_tables
from sec_research.processing.xbrl import normalize_company_facts


def versions() -> ProcessingVersions:
    return ProcessingVersions(
        parser=PARSER_VERSION + "/" + CLASSIFIER_VERSION,
        classifier=CLASSIFIER_VERSION,
        arrow=pa.__version__,
    )


def code_checksum() -> str:
    root = Path(__file__).resolve().parents[1]
    return hashlib.sha256(
        canonical_bytes(
            {
                p.relative_to(root).as_posix(): hashlib.sha256(
                    p.read_bytes().replace(b"\r\n", b"\n")
                ).hexdigest()
                for p in sorted(root.rglob("*.py"))
            }
        )
    ).hexdigest()


def make_spec(
    code_revision: str, lock: Path, run_at: datetime, requests: Sequence[SelectionRequest] = ()
) -> BuildSpec:
    return BuildSpec(
        code_revision=code_revision,
        code_sha256=code_checksum(),
        lock_sha256=hashlib.sha256(lock.read_bytes()).hexdigest(),
        versions=versions(),
        run_at=run_at,
        requests=tuple(sorted(requests, key=lambda r: canonical_bytes(r.model_dump(mode="json")))),
    )


def partition(source: SourceReference) -> str:
    return stable_id("source", source.model_dump(mode="json")).split(":")[1]


def _write(store: LocalDatasets, key: str, rows: Rows) -> list[DatasetObject]:
    return [store.write(name, key, values) for name, values in sorted(rows.items())]


def _read(store: LocalDatasets, items: Sequence[DatasetObject]) -> Rows:
    if len({i.dataset for i in items}) != len(items):
        raise DatasetError("duplicate_partition_dataset")
    return {i.dataset: store.read(i) for i in items}


def selections(store: LocalDatasets, items: Sequence[DatasetObject], spec: BuildSpec) -> Rows:
    results: list[Record] = []
    by_company: dict[str, list[SelectionRequest]] = defaultdict(list)
    for request in spec.requests:
        by_company[request.cik].append(request)
    for cik, requests in sorted(by_company.items()):
        facts: list[FinancialFact] = []
        for item in items:
            if item.dataset == "silver_xbrl_facts":
                facts.extend(
                    f for f in store.read(item) if isinstance(f, FinancialFact) and f.cik == cik
                )
        facts.sort(key=lambda f: f.id or "")
        for request in requests:
            metric = metric_definition(request.metric)
            candidates = [
                f
                for f in facts
                if metric is not None
                and any((f.taxonomy, f.concept) == (c.taxonomy, c.concept) for c in metric.concepts)
            ]
            results.append(
                SelectionEvidence(
                    pipeline_version=PIPELINE,
                    result=select_facts(candidates, request),
                )
            )
    return {"gold_selections": results, "gold_metric_definitions": list(METRICS)}


def build_snapshot(
    bronze: LocalBronze,
    store: LocalDatasets,
    fetches: Sequence[Fetch],
    spec: BuildSpec,
) -> Snapshot:
    """Create immutable objects. Activation is an explicit, separate transaction."""
    if store.root.is_relative_to(bronze.root) or bronze.root.is_relative_to(store.root):
        raise DatasetError("overlapping_bronze_derived_roots")
    spec = BuildSpec.model_validate(spec.model_dump())
    if spec.versions != versions() or spec.code_sha256 != code_checksum():
        raise DatasetError("incompatible_build_environment")
    request_keys = [canonical_bytes(r.model_dump(mode="json")) for r in spec.requests]
    if request_keys != sorted(set(request_keys)):
        raise DatasetError("duplicate_or_unordered_requests")
    if not fetches or len({f.id for f in fetches}) != len(fetches):
        raise DatasetError("empty_or_duplicate_fetches")
    entries: list[SourceEntry] = []
    groups: dict[str, list[SourceEntry]] = defaultdict(list)
    # Audit all inputs before the first derived write, including reference-only metadata.
    for fetch in sorted(fetches, key=lambda f: str(f.id)):
        fetch = Fetch.model_validate(fetch.model_dump())
        expected = fetch.model_dump_json(exclude={"manifest_uri"}).encode()
        if bronze.read_manifest(fetch.id.hex) != expected:
            raise DatasetError("bronze_manifest_mismatch")
        source = validated_source(fetch, bronze.read(fetch.sha256))
        entry = SourceEntry(
            pipeline_version=PIPELINE,
            fetch=fetch,
            source=source,
            disposition="transformed"
            if fetch.source.kind in {"filing", "company_facts"}
            else "reference_only",
        )
        entries.append(entry)
        groups[partition(source)].append(entry)
    silver_objects: list[DatasetObject] = []
    gold_objects: list[DatasetObject] = []
    for key, group in sorted(groups.items()):
        fetch = group[0].fetch
        body = bronze.read(fetch.sha256)
        if fetch.source.kind == "filing":
            rows = html_rows(parse_html(fetch, body), extract_tables(fetch, body))
        elif fetch.source.kind == "company_facts":
            rows = xbrl_rows(normalize_company_facts(fetch, body))
        else:
            rows = {}
        if "silver_provenance" in rows:
            base = rows["silver_provenance"][0]
            rows["silver_provenance"] = [
                SourceProvenance.model_validate(
                    {
                        **base.model_dump(exclude={"id", "fetch_id", "fetched_at"}),
                        "fetch_id": e.fetch.id,
                        "fetched_at": e.fetch.fetched_at,
                    }
                )
                for e in group
            ]
        rows["silver_sources"] = list(group)
        validate_silver(rows, spec.versions)
        objects = _write(store, key, rows)
        silver_objects.extend(objects)
        del rows
        # A fresh Parquet read is the Gold boundary; no Bronze-to-Gold shortcut.
        persisted = _read(store, objects)
        validate_silver(persisted, spec.versions)
        gold_objects.extend(_write(store, key, gold_rows(persisted)))
        del persisted
    gold_objects.extend(_write(store, "catalog", selections(store, silver_objects, spec)))
    inputs = tuple(sorted({e.source.sha256 for e in entries}))
    config_hash = hashlib.sha256(canonical_bytes(spec.model_dump(mode="json"))).hexdigest()
    dataset_version = stable_id(
        "dataset",
        {
            "spec": spec.model_dump(mode="json"),
            "inputs": sorted(e.id for e in entries if e.id is not None),
        },
    )
    common = dict(
        pipeline_version=PIPELINE,
        dataset_version=dataset_version,
        code_revision=spec.code_revision,
        config_sha256=config_hash,
        parser_version=spec.versions.parser,
        normalizer_version=spec.versions.normalizer,
        selection_policy_version=spec.versions.selection,
        input_source_sha256s=inputs,
        state="validated",
        quality="warning",
        validated_at=spec.run_at,
    )
    silver = DatasetPublication.model_validate(
        {
            **common,
            "layer": "silver",
            "objects": sorted(silver_objects, key=lambda i: i.path),
        }
    )
    gold = DatasetPublication.model_validate(
        {
            **common,
            "layer": "gold",
            "objects": sorted(gold_objects, key=lambda i: i.path),
            "input_publication_ids": (silver.id,),
        }
    )
    snapshot = Snapshot(
        pipeline_version=PIPELINE,
        spec=spec,
        source_entries=tuple(sorted(entries, key=lambda e: e.id or "")),
        silver=silver,
        gold=gold,
    )
    # The manifest is the completion marker; partial object writes never create it.
    verify_snapshot(store, snapshot)
    for publication in (silver, gold):
        assert publication.id is not None
        store.put(
            f"manifests/{publication.id.split(':')[1]}.json",
            canonical_bytes(publication.model_dump(mode="json")),
        )
    assert snapshot.id is not None
    store.put(
        f"snapshots/{snapshot.id.split(':')[1]}.json",
        canonical_bytes(snapshot.model_dump(mode="json")),
    )
    return snapshot


def load_snapshot(store: LocalDatasets, snapshot_id: str) -> Snapshot:
    if not snapshot_id.startswith("snapshot:") or len(snapshot_id) != 73:
        raise DatasetError("invalid_snapshot_identity")
    snapshot = Snapshot.model_validate_json(
        store.path(f"snapshots/{snapshot_id.split(':')[1]}.json").read_bytes()
    )
    if snapshot.id != snapshot_id:
        raise DatasetError("snapshot_identity_mismatch")
    for publication in (snapshot.silver, snapshot.gold):
        assert publication.id is not None
        actual = store.path(f"manifests/{publication.id.split(':')[1]}.json").read_bytes()
        if actual != canonical_bytes(publication.model_dump(mode="json")):
            raise DatasetError("publication_manifest_mismatch")
    return snapshot


def verify_snapshot(store: LocalDatasets, snapshot: Snapshot) -> None:
    snapshot = Snapshot.model_validate(snapshot.model_dump())
    if snapshot.spec.versions != versions():
        raise DatasetError("incompatible_snapshot_versions")
    silver: dict[str, list[DatasetObject]] = defaultdict(list)
    gold: dict[str, list[DatasetObject]] = defaultdict(list)
    for publication, dest in ((snapshot.silver, silver), (snapshot.gold, gold)):
        for item in publication.objects:
            pieces = item.path.split("/")
            if len(pieces) != 4 or pieces[0] != "objects" or pieces[1] != item.dataset:
                raise DatasetError("invalid_partition_path")
            dest[pieces[2]].append(item)
    expected: dict[str, list[SourceEntry]] = defaultdict(list)
    for entry in snapshot.source_entries:
        expected[partition(entry.source)].append(entry)
    if set(silver) != set(expected):
        raise DatasetError("incomplete_source_coverage")
    gold_keys = {key for key, group in expected.items() if group[0].disposition == "transformed"}
    if set(gold) != gold_keys | {"catalog"}:
        raise DatasetError("incomplete_gold_coverage")
    for key, entries in expected.items():
        rows = _read(store, silver[key])
        if not same(rows.get("silver_sources", []), entries):
            raise DatasetError("incomplete_source_lineage")
        validate_silver(rows, snapshot.spec.versions)
        actual = _read(store, gold.get(key, []))
        desired = gold_rows(rows)
        if set(actual) != set(desired) or any(not same(actual[k], v) for k, v in desired.items()):
            raise DatasetError("invalid_gold_transformation")
    actual = _read(store, gold["catalog"])
    desired = selections(store, snapshot.silver.objects, snapshot.spec)
    if set(actual) != set(desired) or any(not same(actual[k], v) for k, v in desired.items()):
        raise DatasetError("invalid_selection_evidence")


def record_counts(snapshot: Snapshot) -> dict[str, int]:
    result: dict[str, int] = defaultdict(int)
    for item in (*snapshot.silver.objects, *snapshot.gold.objects):
        result[item.dataset] += item.row_count
    return dict(sorted(result.items()))
