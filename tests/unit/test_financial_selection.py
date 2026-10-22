from datetime import date
from itertools import permutations

import pytest

from sec_research.contracts.canonical import FinancialFact, ReportingPeriod
from sec_research.contracts.xbrl import SelectionRequest
from sec_research.domain.financial_selection import select_facts
from sec_research.domain.periods import assess_period
from sec_research.processing.xbrl import normalize_company_facts
from tests.xbrl_helpers import body_for, input_facts, raw_fact


def facts_for(rows: list[dict[str, object]], **kwargs: str) -> list[FinancialFact]:
    body = body_for(rows, **kwargs)
    return [
        r.fact
        for r in normalize_company_facts(input_facts(body), body).observations
        if r.fact is not None
    ]


def request_for(**updates: object) -> SelectionRequest:
    return SelectionRequest.model_validate(
        {
            "cik": "0000000001",
            "metric": "net_income",
            "period": {
                "kind": "duration",
                "start": "2024-01-01",
                "end": "2024-12-31",
                "duration_class": "unknown",
            },
            "as_of": "2026-12-31",
            **updates,
        }
    )


def test_original_latest_cutoff_and_comparison_preserve_reporting_versions() -> None:
    facts = facts_for(
        [
            raw_fact(),
            raw_fact(),
            raw_fact(val=43, accn="0000000001-26-000001", filed="2026-02-01", fy=2025),
        ]
    )
    for mode, expected in (("original", 42), ("latest_as_of", 43)):
        result = select_facts(facts, request_for(mode=mode))
        assert result.status == "selected" and result.selected[0].value == expected
        assert len(result.alternatives) == 3
    result = select_facts(facts, request_for(as_of="2025-02-01"))
    assert result.selected[0].value == 42
    assert select_facts(facts, request_for(as_of="2025-01-31")).status == "unavailable"
    comparison = select_facts(facts, request_for(mode="compare_versions"))
    assert len(comparison.selected) == 2 and comparison.status == "compared"
    assert "later_reporting_does_not_prove_restatement" in comparison.reasons


def test_conflicting_candidates_never_promoted() -> None:
    for accession in ("0000000001-25-000001", "0000000001-25-000002"):
        facts = facts_for([raw_fact(), raw_fact(val=43, accn=accession)])
        result = select_facts(facts, request_for())
        assert result.status == "ambiguous" and not result.selected
        assert len(result.alternatives) == 2


def test_permutation_and_future_fact_invariance() -> None:
    facts = facts_for(
        [
            raw_fact(),
            raw_fact(accn="0000000001-25-000002"),
            raw_fact(val=99, accn="0000000001-26-000001", filed="2026-02-01"),
        ]
    )
    query = request_for(as_of="2025-02-01")
    expected = select_facts(facts, query)
    for order in permutations(facts):
        assert select_facts(order, query) == expected
    assert select_facts(facts[:2], query).selected == expected.selected
    assert expected.selected[0].accession == "0000000001-25-000001"


@pytest.mark.parametrize(
    ("query", "reason"),
    [
        ({"cik": "0000000002"}, "company_mismatch"),
        ({"form": "10-Q"}, "form_mismatch"),
        ({"context_policy": "verified_consolidated"}, "unverified_context"),
        ({"metric": "operating_income"}, "unsupported_metric_concept"),
        ({"period": {"kind": "instant", "end": "2024-12-31"}}, "period_kind_mismatch"),
    ],
)
def test_eligibility_explanations(query: dict[str, object], reason: str) -> None:
    result = select_facts(facts_for([raw_fact()]), request_for(**query))
    assert result.status in {"unavailable", "unsupported"} and reason in result.decisions[0].reasons


def test_units_aliases_and_unknown_metric() -> None:
    facts = facts_for([raw_fact()], unit="EUR")
    assert "unit_mismatch" in select_facts(facts, request_for()).decisions[0].reasons
    facts = facts_for([raw_fact()])
    assert select_facts(facts, request_for(metric="net_income_loss")).selected == (
        select_facts(facts, request_for()).selected
    )
    assert select_facts(facts, request_for(metric="income")).status == "unsupported"
    revenue = facts_for([raw_fact()], concept="Revenues")
    assert select_facts(revenue, request_for(metric="revenue")).status == "unsupported"


def test_failed_quality_dimensions_and_timestamp_cutoff() -> None:
    original = facts_for([raw_fact()])[0]

    def changed(**updates: object) -> FinancialFact:
        return FinancialFact.model_validate({**original.model_dump(), "id": None, **updates})

    failed = changed(quality="failed")
    dimensional = changed(
        context_status="verified",
        context_id="ctx",
        dimensions=[{"axis": "Segment", "member": "Retail"}],
    )
    after = changed(accepted_at="2025-02-02T00:01:00Z")
    for fact, reason in (
        (failed, "failed_quality"),
        (dimensional, "dimensional_context"),
        (after, "after_as_of"),
    ):
        result = select_facts([fact], request_for(as_of="2025-02-01"))
        assert result.status == "unavailable" and reason in result.decisions[0].reasons
    verified = changed(context_status="verified", context_id="ctx", dimensions=[])
    assert select_facts([verified], request_for(context_policy="verified_consolidated")).status == (
        "selected"
    )


def test_amendment_and_non_equivalent_concepts() -> None:
    facts = facts_for(
        [
            raw_fact(val=0),
            raw_fact(val=-7, form="10-K/A", accn="0000000001-25-000002", filed="2025-03-01"),
        ]
    )
    assert select_facts(facts, request_for()).selected[0].value == -7
    assert select_facts(facts, request_for(form="10-K")).selected[0].value == 0
    assert select_facts(facts, request_for(mode="original")).selected[0].value == 0
    wrong = facts_for([raw_fact()], concept="ProfitLoss")
    assert select_facts(wrong, request_for()).status == "unsupported"


def test_quarter_ytd_annual_and_comparative_exact_dates() -> None:
    facts = facts_for(
        [
            raw_fact(start="2024-04-01", end="2024-06-30", val=1, form="10-Q"),
            raw_fact(end="2024-06-30", val=2, form="10-Q"),
            raw_fact(val=3),
            raw_fact(start="2023-01-01", end="2023-12-31", val=4),
        ]
    )
    for start, end, expected in [
        ("2024-04-01", "2024-06-30", 1),
        ("2024-01-01", "2024-06-30", 2),
        ("2024-01-01", "2024-12-31", 3),
        ("2023-01-01", "2023-12-31", 4),
    ]:
        query = request_for(
            period={"kind": "duration", "start": start, "end": end, "duration_class": "unknown"}
        )
        assert select_facts(facts, query).selected[0].value == expected


@pytest.mark.parametrize(
    ("start", "end", "shape", "days"),
    [
        ("2024-01-01", "2024-12-31", "annual_length", 366),
        ("2022-12-25", "2023-12-30", "annual_length", 371),
        ("2023-12-31", "2024-12-28", "annual_length", 364),
        ("2024-01-01", "2024-06-30", "half_year_length", 182),
        ("2024-01-01", "2024-09-30", "nine_month_length", 274),
        ("2024-01-01", "2024-03-31", "quarter_length", 91),
        ("2024-01-01", "2024-01-01", "other", 1),
    ],
)
def test_interval_shapes_are_diagnostics_not_fiscal_inference(
    start: str,
    end: str,
    shape: str,
    days: int,
) -> None:
    period = ReportingPeriod(
        kind="duration",
        start=date.fromisoformat(start),
        end=date.fromisoformat(end),
        duration_class="unknown",
    )
    assessment = assess_period(period)
    assert assessment.shape == shape and assessment.days == days
    assert period.duration_class == "unknown"
