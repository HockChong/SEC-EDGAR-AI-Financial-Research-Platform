"""Offline Company Facts audit. Diagnostic JSON is not Silver/Gold publication."""

import argparse
import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path

from sec_research.adapters.storage.local import LocalBronze
from sec_research.contracts.canonical import ReportingPeriod, canonical_bytes
from sec_research.contracts.xbrl import NormalizedFacts, SelectionRequest
from sec_research.domain.financial_selection import select_facts
from sec_research.domain.metrics import METRICS
from sec_research.processing.corpus import audit_bronze
from sec_research.processing.xbrl import (
    compact_json,
    normalize_company_facts,
    resolve_pointer,
    source_json,
)


def selection_examples(result: NormalizedFacts, as_of: date) -> list[dict[str, object]]:
    facts = [r.fact for r in result.observations if r.fact is not None]
    annual = [
        f
        for f in facts
        if f.concept == "NetIncomeLoss"
        and f.taxonomy == "us-gaap"
        and f.form == "10-K"
        and f.filed <= as_of
        and f.period.start is not None
        and 350 <= (f.period.end - f.period.start).days + 1 <= 380
    ]
    if not annual:
        return []
    anchor = max(annual, key=lambda f: (f.period.end, f.filed, f.accession))
    examples: list[dict[str, object]] = []
    for metric in METRICS:
        period = (
            ReportingPeriod(kind="instant", end=anchor.period.end)
            if metric.period_kind == "instant"
            else anchor.period
        )
        request = SelectionRequest(
            cik=result.company.cik, metric=metric.metric_name, period=period, as_of=as_of
        )
        candidates = [
            f
            for f in facts
            if any(f.taxonomy == c.taxonomy and f.concept == c.concept for c in metric.concepts)
        ]
        selection = select_facts(candidates, request)
        examples.append(
            {
                "request": request.model_dump(mode="json"),
                "status": selection.status,
                "quality": selection.quality,
                "metric_id": selection.metric_id,
                "reasons": selection.reasons,
                "candidate_decisions": dict(
                    Counter(reason for d in selection.decisions for reason in d.reasons)
                ),
                "eligible_occurrences": len(selection.alternatives),
                "selected": [f.model_dump(mode="json") for f in selection.selected],
            }
        )
    return examples


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path(".runtime/artifacts"))
    parser.add_argument("--inventory", type=Path, default=Path("docs/bronze-corpus-inventory.json"))
    parser.add_argument("--as-of", type=date.fromisoformat, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--examples", type=Path, help="Optional source-linked regression examples")
    args = parser.parse_args(argv)
    store = LocalBronze(args.artifact_root)
    if args.output.resolve().is_relative_to(store.root):
        raise ValueError("diagnostics must remain outside immutable Bronze storage")
    fetches = audit_bronze(store, args.inventory)
    selected = sorted(
        (f for f in fetches if f.source.kind == "company_facts"),
        key=lambda f: (f.source.cik or "", f.sha256, str(f.id)),
    )
    if not selected:
        raise ValueError("inventory contains no Company Facts")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_dir = args.output.parent / (args.output.stem + "-observations")
    output_dir.mkdir(exist_ok=True)
    rows: list[dict[str, object]] = []
    examples_data = json.loads(args.examples.read_bytes())["cases"] if args.examples else []
    verified_examples: set[str] = set()
    for fetch in selected:
        body = store.read(fetch.sha256)
        result = normalize_company_facts(fetch, body)
        logical = result.logical_bytes()
        logical_hash = hashlib.sha256(logical).hexdigest()
        if logical != normalize_company_facts(fetch, body).logical_bytes():
            raise ValueError("nondeterministic Company Facts normalization")
        encoded = result.model_dump_json().encode()
        if NormalizedFacts.model_validate_json(encoded).logical_bytes() != logical:
            raise ValueError("Company Facts round trip changed logical output")
        data = source_json(body)
        for case in examples_data:
            if case["source_sha256"] != fetch.sha256:
                continue
            if case["source_url"] != fetch.source.url or case["cik"] != fetch.source.cik:
                raise ValueError("regression example source identity mismatch")
            original = resolve_pointer(data, case["source_pointer"])
            if compact_json(original) != case["raw_json"]:
                raise ValueError("regression example differs from original source")
            verified_examples.add(case["case_id"])
        for occurrence in result.observations:
            if compact_json(resolve_pointer(data, occurrence.locator.path)) != occurrence.raw_json:
                raise ValueError("source observation pointer mismatch")
        for concept in result.concepts:
            definition = resolve_pointer(data, concept.locator.path)
            if not isinstance(definition, dict) or (
                definition.get("label") != concept.label
                or definition.get("description") != concept.description
            ):
                raise ValueError("concept metadata pointer mismatch")
        target = output_dir / f"{result.company.cik}-{fetch.sha256}.json"
        target.write_bytes(encoded)
        examples = selection_examples(result, args.as_of)
        rows.append(
            {
                "cik": result.company.cik,
                "company": result.company.legal_name,
                "source_sha256": fetch.sha256,
                "source_url": fetch.source.url,
                "logical_sha256": logical_hash,
                "output_sha256": hashlib.sha256(encoded).hexdigest(),
                "observations": len(result.observations),
                "concepts": len(result.concepts),
                "taxonomy_counts": dict(
                    Counter(r.locator.path.split("/")[2] for r in result.observations)
                ),
                "quality_counts": dict(Counter(r.quality for r in result.observations)),
                "reason_counts": dict(
                    Counter(reason for r in result.observations for reason in r.reasons)
                ),
                "period_shapes": dict(
                    Counter(
                        r.period_assessment.shape
                        for r in result.observations
                        if r.period_assessment is not None
                    )
                ),
                "source_pointers_verified": len(result.observations),
                "deterministic_replay": True,
                "selection_status_counts": dict(Counter(str(e["status"]) for e in examples)),
                "selection_examples": examples,
            }
        )
        print(f"{result.company.cik}: {len(result.observations)} source observations", flush=True)
    audit_bronze(store, args.inventory)
    if len(verified_examples) != len(examples_data):
        raise ValueError("not all regression examples resolved uniquely")
    report = {
        "schema_version": "wp34-diagnostics-1",
        "as_of": args.as_of.isoformat(),
        "normalizer_version": "company-facts-1",
        "catalog_version": "reported-metrics-1",
        "selection_policy": "fact-selection-1",
        "period_policy": "period-boundaries-1",
        "bronze_fetches_verified": len(fetches),
        "bronze_unchanged": True,
        "integrity_quality": "passed",
        "regression_examples_verified": len(verified_examples),
        "source_code_sha256": {
            str(p).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(
                [
                    *Path("src/sec_research/domain").glob("*.py"),
                    *Path("src/sec_research/processing").glob("xbrl*.py"),
                    Path("src/sec_research/contracts/xbrl.py"),
                    Path("src/sec_research/contracts/canonical.py"),
                ]
            )
        },
        "lock_sha256": hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest(),
        "dataset_input_sha256": hashlib.sha256(
            canonical_bytes([(f.source.cik, f.sha256) for f in selected])
        ).hexdigest(),
        "independent_financial_adjudication": "not_performed",
        "wp33_financial_adjudication": "owner_deferred_unresolved_findings_preserved",
        "rows": rows,
    }
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
