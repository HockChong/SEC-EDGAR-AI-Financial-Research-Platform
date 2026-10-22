"""Offline WP3.3 diagnostics and unadjudicated review candidates; never publishes datasets."""

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from sec_research.adapters.storage.local import LocalBronze
from sec_research.contracts.tables import TableExtraction
from sec_research.processing.corpus import audit_bronze
from sec_research.processing.dom import load_dom, locator, resolve
from sec_research.processing.table_grid import cell_text, nearest, visible
from sec_research.processing.tables import EXTRACTOR_VERSION, extract_tables


def verify_sources(result: TableExtraction, body: bytes) -> int:
    """Independently enumerate DOM tables/cells, then check paths and raw lexical content."""
    if (
        hashlib.sha256(body).hexdigest() != result.document.source.sha256
        or len(body) != result.document.source.byte_count
    ):
        raise ValueError("table audit source integrity mismatch")
    root = load_dom(body).root
    expected = [locator(n) for n in root.iter("table") if visible(n)]
    if [t.locator.path for t in result.tables] != expected:
        raise ValueError("table enumeration mismatch")
    count = 0
    for item in result.tables:
        table = resolve(root, item.locator.path)
        expected_cells = [
            locator(n)
            for n in table.iter()
            if n.tag in {"td", "th"} and nearest(n, "table") is table and visible(n)
        ]
        if [c.locator.path for c in item.raw_cells] != expected_cells:
            raise ValueError("cell enumeration mismatch")
        if item.title_source is not None:
            resolve(root, item.title_source.path)
        for cell in item.raw_cells:
            node = resolve(root, cell.locator.path)
            if cell_text(node) != cell.raw_text:
                raise ValueError("cell lexical source mismatch")
            if (
                node.get("rowspan") != cell.rowspan_attribute
                or node.get("colspan") != cell.colspan_attribute
            ):
                raise ValueError("cell span source mismatch")
            count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path(".runtime/artifacts"))
    parser.add_argument("--inventory", type=Path, default=Path("docs/bronze-corpus-inventory.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    store = LocalBronze(args.artifact_root)
    if args.output.resolve().is_relative_to(store.root):
        raise ValueError("diagnostics must not be written inside immutable Bronze storage")
    fetches = audit_bronze(store, args.inventory)
    output_dir = args.output.parent / (args.output.stem + "-documents")
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    candidates: dict[str, list[dict[str, object]]] = defaultdict(list)
    totals: Counter[str] = Counter()
    for fetch in fetches:
        filing = fetch.source.filing
        if filing is None:
            continue
        body = store.read(fetch.sha256)
        result = extract_tables(fetch, body)
        logical = result.logical_bytes()
        if logical != extract_tables(fetch, body).logical_bytes():
            raise ValueError("table extraction replay mismatch")
        TableExtraction.model_validate_json(result.model_dump_json())
        verified = verify_sources(result, body)
        sections = {s.id: s for s in result.sections}
        kinds = Counter(t.kind for t in result.tables)
        stats = Counter(
            {
                "detected": len(result.tables),
                "reconstructed": sum(t.table is not None for t in result.tables),
                "quarantined": sum(t.table is None for t in result.tables),
                "nested": sum(t.parent_table_path is not None for t in result.tables),
                "raw_cells_verified": verified,
                "grid_cells": sum(len(t.cells) for t in result.tables),
                "header_cells": sum(c.is_header for t in result.tables for c in t.cells),
                "cells_with_column_headers": sum(
                    bool(c.column_header_ids) for t in result.tables for c in t.contexts
                ),
                "cells_with_period_labels": sum(
                    bool(c.period_labels) for t in result.tables for c in t.contexts
                ),
                "merged_cells": sum(
                    c.row_span > 1 or c.column_span > 1 for t in result.tables for c in t.cells
                ),
                "unknown_section_tables": sum(
                    t.section_id is None or sections[t.section_id].classification != "classified"
                    for t in result.tables
                ),
            }
        )
        totals.update(stats)
        numeric = Counter(c.normalization.status for t in result.tables for c in t.contexts)
        totals.update({f"normalization_{status}": count for status, count in numeric.items()})
        totals.update(kinds)
        warnings = Counter(w for t in result.tables for w in t.warnings)
        output_file = output_dir / f"{filing.accession}.json"
        output_file.write_bytes(result.model_dump_json().encode())
        rows.append(
            {
                "cik": filing.cik,
                "accession": filing.accession,
                "form": filing.form,
                "source_sha256": fetch.sha256,
                "document_id": result.document.id,
                "logical_sha256": hashlib.sha256(logical).hexdigest(),
                "deterministic_replay": True,
                "counts": dict(stats),
                "normalization": dict(numeric),
                "kinds": dict(kinds),
                "warnings": dict(warnings),
            }
        )
        for item in result.tables:
            if item.table is None or item.kind not in {
                "financial_statement",
                "financial_disclosure",
            }:
                continue
            title = item.title.casefold()
            family = (
                "cash_flow"
                if "cash flow" in title
                else "balance_sheet"
                if "balance sheet" in title
                else "income"
                if re.search(r"income|operations|earnings", title)
                else "disclosure"
            )
            candidates[filing.cik].append(
                {
                    "cik": filing.cik,
                    "accession": filing.accession,
                    "form": filing.form,
                    "source_sha256": fetch.sha256,
                    "source_url": fetch.source.url,
                    "document_id": result.document.id,
                    "table_id": item.table.id,
                    "path": item.locator.path,
                    "title": item.title,
                    "predicted_kind": item.kind,
                    "candidate_family": family,
                    "section_classification": sections[item.section_id].classification
                    if item.section_id
                    else "unknown",
                    "merged": any(c.row_span > 1 or c.column_span > 1 for c in item.cells),
                    "multi_period": len({p for c in item.contexts for p in c.period_labels}) > 1,
                    "shape": [item.table.rows, item.table.columns],
                    "sample_cells": [c.model_dump(mode="json") for c in item.cells[:16]],
                    "warnings": list(item.warnings),
                    "human_adjudication": "pending",
                    "expected_structure": None,
                    "expected_financial_interpretation": None,
                }
            )
        print(
            f"{filing.accession}: {len(result.tables)} tables; {stats['quarantined']} quarantined",
            flush=True,
        )
    audit_bronze(store, args.inventory)
    # Review candidates are predictions for adjudication, never accuracy ground truth.
    samples: list[dict[str, object]] = []
    for cik, pool in sorted(candidates.items()):
        selected: list[dict[str, object]] = []
        for family in ("income", "balance_sheet", "cash_flow"):
            match = next((c for c in pool if c["candidate_family"] == family), None)
            if match is not None:
                selected.append(match)
        # Explicitly include both JPMorgan quarters whose section metadata is incomplete.
        if cik == "0000019617":
            for accession in ("0001628280-26-029344", "0001628280-26-054343"):
                match = next(
                    (
                        c
                        for c in pool
                        if c["accession"] == accession
                        and c["section_classification"] == "unclassified"
                        and c["candidate_family"] in {"income", "balance_sheet", "cash_flow"}
                    ),
                    None,
                )
                if match is not None and match not in selected:
                    selected.append(match)
        for flag in ("multi_period", "merged"):
            match = next((c for c in pool if c[flag] and c not in selected), None)
            if match is not None and len(selected) < 5:
                selected.append(match)
        for candidate in pool:
            if len(selected) >= 5:
                break
            if candidate not in selected:
                selected.append(candidate)
        samples.extend(selected)
    report = {
        "schema_version": "wp33-diagnostics-2",
        "extractor_version": EXTRACTOR_VERSION,
        "executed_at_utc": datetime.now(UTC).isoformat(),
        "filings": len(rows),
        "bronze_fetches_verified": len(fetches),
        "bronze_objects_verified": len(store.checksums()),
        "bronze_unchanged_after_extraction": True,
        "normalization_complete": True,
        "normalization_policy_version": "table-numeric-1",
        "human_adjudicated": False,
        "counts": dict(totals),
        "rows": rows,
        "inventory_sha256": hashlib.sha256(args.inventory.read_bytes()).hexdigest(),
        "lock_sha256": hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest(),
        "code_sha256": {
            str(p).replace("\\", "/"): hashlib.sha256(
                p.read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            for p in sorted(
                [
                    *Path("src/sec_research/processing").glob("*.py"),
                    *Path("src/sec_research/contracts").glob("*.py"),
                ]
            )
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output.with_name(args.output.stem + "-samples.json").write_text(
        json.dumps({"human_adjudicated": False, "cases": samples}, indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
