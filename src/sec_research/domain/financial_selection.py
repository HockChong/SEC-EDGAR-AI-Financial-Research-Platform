"""Exact-period, accession-preserving selection with explicit abstention."""

from collections import defaultdict
from collections.abc import Iterable

from sec_research.contracts.canonical import FinancialFact
from sec_research.contracts.xbrl import CandidateDecision, FactSelection, SelectionRequest
from sec_research.domain.metrics import metric_definition


def select_facts(facts: Iterable[FinancialFact], request: SelectionRequest) -> FactSelection:
    request = SelectionRequest.model_validate(request.model_dump())
    metric = metric_definition(request.metric)
    if metric is None:
        return FactSelection(
            request=request,
            metric_id=None,
            status="unsupported",
            quality="warning",
            reasons=("unsupported_metric",),
        )
    decisions: list[CandidateDecision] = []
    eligible: dict[str, FinancialFact] = {}
    for raw in facts:
        fact = FinancialFact.model_validate(raw.model_dump())
        reasons: list[str] = []
        if fact.cik != request.cik:
            reasons.append("company_mismatch")
        if not any(
            c.taxonomy == fact.taxonomy and c.concept == fact.concept for c in metric.concepts
        ):
            reasons.append("unsupported_metric_concept")
        if fact.period.kind != metric.period_kind or request.period.kind != metric.period_kind:
            reasons.append("period_kind_mismatch")
        if (fact.period.start, fact.period.end) != (request.period.start, request.period.end):
            reasons.append("period_boundaries_mismatch")
        if fact.unit != metric.unit or fact.currency != "USD":
            reasons.append("unit_mismatch")
        if fact.form not in {"10-K", "10-Q", "10-K/A", "10-Q/A"} or (
            request.form is not None and fact.form != request.form
        ):
            reasons.append("form_mismatch")
        if fact.filed > request.as_of or (
            fact.accepted_at is not None and fact.accepted_at.date() > request.as_of
        ):
            reasons.append("after_as_of")
        if fact.quality == "failed":
            reasons.append("failed_quality")
        if fact.context_status == "verified" and fact.dimensions != ():
            reasons.append("dimensional_context")
        if request.context_policy == "verified_consolidated" and fact.context_status != "verified":
            reasons.append("unverified_context")
        assert fact.id is not None
        decisions.append(
            CandidateDecision(
                fact_id=fact.id,
                observation_id=fact.observation_id,
                eligible=not reasons,
                reasons=tuple(reasons) or ("eligible_exact_reported_fact",),
            )
        )
        if not reasons:
            eligible[fact.id] = fact
    alternatives = tuple(
        sorted(eligible.values(), key=lambda f: (f.filed, f.accession, f.id or ""))
    )
    common = {
        "request": request,
        "metric_id": metric.id,
        "alternatives": alternatives,
        "decisions": tuple(sorted(decisions, key=lambda d: d.fact_id)),
    }
    if not alternatives:
        unsupported = not any(
            "company_mismatch" not in decision.reasons
            and "unsupported_metric_concept" not in decision.reasons
            for decision in decisions
        )
        return FactSelection.model_validate(
            {
                **common,
                "status": "unsupported" if unsupported else "unavailable",
                "quality": "warning",
                "reasons": (
                    ("no_supported_company_concept",)
                    if unsupported
                    else ("no_eligible_observations",)
                ),
            }
        )
    # One accession cannot legitimately select two incompatible reportings of this metric/period.
    by_accession: dict[str, list[FinancialFact]] = defaultdict(list)
    for fact in alternatives:
        by_accession[fact.accession].append(fact)
    if any(len({f.observation_id for f in group}) > 1 for group in by_accession.values()):
        return FactSelection.model_validate(
            {
                **common,
                "status": "ambiguous",
                "quality": "warning",
                "reasons": ("conflicting_accession_observations",),
            }
        )
    # Deduplicate occurrences, retaining every source link in alternatives/decisions.
    versions = [min(group, key=lambda f: f.id or "") for group in by_accession.values()]
    if request.mode == "compare_versions":
        selected = tuple(versions)
        status = "compared"
    else:
        boundary = (min if request.mode == "original" else max)(f.filed for f in versions)
        finalists = [f for f in versions if f.filed == boundary]
        if len({f.value for f in finalists}) != 1:
            return FactSelection.model_validate(
                {
                    **common,
                    "status": "ambiguous",
                    "quality": "warning",
                    "reasons": ("conflicting_same_day_reportings",),
                }
            )
        selected = (min(finalists, key=lambda f: (f.accession, f.id or "")),)
        status = "selected"
    warnings = [
        "date_cutoff_end_of_day_utc",
        "historical_api_coverage_not_reconstructed",
        "later_reporting_does_not_prove_restatement",
        "exact_period_and_unit_match",
        "equivalent_ties_accession_then_fact_id",
    ]
    if any(f.context_status == "unknown" for f in selected):
        warnings.append("company_facts_entity_scope_context_unverified")
    return FactSelection.model_validate(
        {
            **common,
            "status": status,
            "quality": "warning",
            "selected": selected,
            "reasons": tuple(warnings),
        }
    )
