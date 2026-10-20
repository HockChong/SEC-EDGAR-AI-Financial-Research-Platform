"""Read-only Bronze audit and offline WP3.2 diagnostics. Outputs are not Silver publication."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from sec_research.adapters.storage.local import LocalBronze
from sec_research.contracts.bronze import validated_source
from sec_research.contracts.parsing import ParsedDocument
from sec_research.ingestion.ports import Fetch
from sec_research.processing.benchmark import Benchmark, CorpusCase, CorpusSplit, score_boundaries
from sec_research.processing.dom import ParseError, load_dom, resolve
from sec_research.processing.html import parse_html


def audit_bronze(store: LocalBronze, inventory: Path) -> list[Fetch]:
    """Compare stored immutable manifests/objects with the separately recorded inventory."""
    data = json.loads(inventory.read_bytes())
    fetches = [Fetch.model_validate(f) for f in data["fetches"]]
    if len({f.id for f in fetches}) != len(fetches):
        raise ValueError("duplicate fetch identities in inventory")
    known: set[str] = set()
    manifest_ids: set[str] = set()
    for fetch in fetches:
        expected = fetch.model_dump_json(exclude={"manifest_uri"}).encode()
        if store.read_manifest(fetch.id.hex) != expected:
            raise ValueError("stored manifest differs from inventory")
        validated_source(fetch, store.read(fetch.sha256))
        known.add(fetch.sha256)
        manifest_ids.add(fetch.id.hex)
    actual_manifests = {p.stem for p in (store.root / "bronze/manifests").glob("*.json")}
    if known != set(store.checksums()) or actual_manifests != manifest_ids:
        raise ValueError("missing or orphaned Bronze object/manifest")
    return fetches


def diagnose(
    fetch: Fetch, body: bytes, case: CorpusCase, benchmark: Benchmark
) -> tuple[ParsedDocument, dict[str, object]]:
    start = perf_counter()
    result = parse_html(fetch, body)
    logical_hash = hashlib.sha256(result.logical_bytes()).hexdigest()
    if result.logical_bytes() != parse_html(fetch, body).logical_bytes():
        raise ValueError("nondeterministic parse")
    dom = load_dom(body)
    normalized = "\n".join(b.text for b in result.blocks)
    for block in result.blocks:
        resolve(dom.root, block.locator.path)
        if normalized[block.locator.start : block.locator.end] != block.text:
            raise ValueError("invalid normalized reading-order offsets")
    # Revalidate deserialization, including canonical identities and complete graph ownership.
    ParsedDocument.model_validate_json(result.model_dump_json())
    labeled = next((c for c in benchmark.cases if c.accession == case.accession), None)
    if labeled is not None and labeled.split != case.split:
        raise ValueError("benchmark split mismatch")
    scores = score_boundaries(result, dom, labeled) if labeled is not None else []
    return result, {
        **case.model_dump(mode="json"),
        "status": "parsed",
        "encoding": result.encoding,
        "parser_version": result.document.parser_version,
        "document_id": result.document.id,
        "logical_sha256": logical_hash,
        "deterministic_replay": True,
        "block_count": len(result.blocks),
        "block_kinds": dict(Counter(b.kind for b in result.blocks)),
        "locators_verified": len(result.blocks),
        "section_count": len(result.sections),
        "classified_sections": [
            f"{s.part}:{s.item}" for s in result.sections if s.classification == "classified"
        ],
        "unclassified_blocks": sum(
            s.last_block_ordinal - s.first_block_ordinal + 1
            for s in result.sections
            if s.classification != "classified"
        ),
        "warnings": dict(Counter(e.reason_code for e in result.quality_events)),
        "boundary_scores": scores,
        "diagnostic_seconds": round(perf_counter() - start, 3),
    }


def aggregate(rows: list[dict[str, object]]) -> dict[str, object]:
    """Explicit denominators; structural coverage never masquerades as accuracy."""
    slices: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        for key in ("all", f"form:{row['form']}", f"company:{row['cik']}", f"split:{row['split']}"):
            stats = slices[key]
            for field in (
                "parsed",
                "failed",
                "labeled_boundaries",
                "exact_boundaries",
                "correct_starts",
                "correct_ends",
            ):
                stats.setdefault(field, 0)
            stats["filings"] += 1
            stats["parsed" if row["status"] == "parsed" else "failed"] += 1
            warnings = row.get("warnings", {})
            assert isinstance(warnings, dict)
            stats["warning_events"] += sum(int(v) for v in warnings.values())
            for reason, count in warnings.items():
                stats[f"warning:{reason}"] += int(count)
            if row["status"] != "parsed":
                stats[f"failure:{row['code']}"] += 1
            scores = row.get("boundary_scores", [])
            assert isinstance(scores, list)
            for score in scores:
                stats["labeled_boundaries"] += 1
                stats["exact_boundaries"] += int(score["both_correct"])
                stats["correct_starts"] += int(score["start_correct"])
                stats["correct_ends"] += int(score["end_correct"])
        scores = row.get("boundary_scores", [])
        assert isinstance(scores, list)
        for score in scores:
            key = f"section:{row['form']}:{score['part']}:{score['item']}"
            slices[key]["labeled_boundaries"] += 1
            slices[key]["exact_boundaries"] += int(score["both_correct"])
        detected = row.get("classified_sections", [])
        assert isinstance(detected, list)
        for section in detected:
            slices[f"structural_section:{row['form']}:{section}"]["detected_occurrences"] += 1
    return {key: dict(value) for key, value in sorted(slices.items())}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path(".runtime/artifacts"))
    parser.add_argument("--inventory", type=Path, default=Path("docs/bronze-corpus-inventory.json"))
    parser.add_argument(
        "--split-file", type=Path, default=Path("tests/fixtures/parsing/corpus-split.json")
    )
    parser.add_argument(
        "--benchmark", type=Path, default=Path("tests/fixtures/parsing/boundaries.json")
    )
    parser.add_argument(
        "--split", choices=("development", "held_out", "all"), default="development"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    split = CorpusSplit.model_validate_json(args.split_file.read_bytes())
    benchmark = Benchmark.model_validate_json(args.benchmark.read_bytes())
    store = LocalBronze(args.artifact_root)
    if args.output.resolve().is_relative_to(store.root):
        raise ValueError("diagnostics must not be written inside immutable Bronze storage")
    fetches = audit_bronze(store, args.inventory)
    by_accession = {f.source.filing.accession: f for f in fetches if f.source.filing is not None}
    if set(by_accession) != {c.accession for c in split.filings}:
        raise ValueError("corpus split must cover every stored filing")
    rows: list[dict[str, object]] = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_dir = args.output.parent / (args.output.stem + "-documents")
    output_dir.mkdir(exist_ok=True)
    for case in split.filings:
        if args.split != "all" and case.split != args.split:
            continue
        fetch = by_accession[case.accession]
        if (
            fetch.sha256 != case.source_sha256
            or fetch.source.cik != case.cik
            or (fetch.source.filing is None or fetch.source.filing.form != case.form)
        ):
            raise ValueError("corpus case source mismatch")
        try:
            result, row = diagnose(fetch, store.read(fetch.sha256), case, benchmark)
            (output_dir / f"{case.accession}.json").write_bytes(result.model_dump_json().encode())
        except ParseError as error:
            row = {**case.model_dump(mode="json"), "status": "failed", "code": error.code}
        rows.append(row)
        print(f"{case.accession}: {row['status']}", flush=True)
    audit_bronze(store, args.inventory)
    report = {
        "schema_version": "wp32-diagnostics-1",
        "executed_at_utc": datetime.now(UTC).isoformat(),
        "source_code_sha256": {
            str(path.relative_to(Path(__file__).parents[1])).replace("\\", "/"): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(
                [
                    *Path(__file__).parent.glob("*.py"),
                    *Path(__file__).parents[1].joinpath("contracts").glob("*.py"),
                ]
            )
        },
        "corpus_filings": len(by_accession),
        "bronze_fetches_verified": len(fetches),
        "bronze_objects_verified": len(store.checksums()),
        "bronze_orphans": 0,
        "bronze_unchanged_after_parsing": True,
        "split_sha256": hashlib.sha256(args.split_file.read_bytes()).hexdigest(),
        "benchmark_sha256": hashlib.sha256(args.benchmark.read_bytes()).hexdigest(),
        "lock_sha256": hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest(),
        "rows": rows,
        "metrics": aggregate(rows),
    }
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return int(any(row["status"] != "parsed" for row in rows))


if __name__ == "__main__":
    raise SystemExit(main())
