"""Small catalog of exact reported concepts, with deliberately narrow meanings."""

from typing import Literal

from sec_research.contracts.canonical import ConceptMapping, MetricDefinition

CATALOG_VERSION = "reported-metrics-1"
SELECTION_POLICY = "fact-selection-1"


def _metric(
    name: str, concept: str, kind: Literal["instant", "duration"], description: str
) -> MetricDefinition:
    return MetricDefinition(
        pipeline_version="xbrl-1",
        metric_name=name,
        metric_version=CATALOG_VERSION,
        description=description,
        mapping_status="supported",
        concepts=(ConceptMapping(taxonomy="us-gaap", concept=concept, priority=0),),
        period_kind=kind,
        unit="USD",
        context_requirement="company_facts_entity",
        selection_policy_version=SELECTION_POLICY,
        sign_policy="as_reported",
        denominator_policy="not_applicable",
        rounding_policy="none",
        limitations=(
            "Company Facts entity scope; XBRL dimensions remain unknown",
            "Reported concept only; no cross-concept or cross-issuer equivalence implied",
        ),
    )


METRICS = (
    _metric(
        "revenue",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "duration",
        "Revenue from customer contracts excluding assessed tax; not total bank revenue",
    ),
    _metric("net_income", "NetIncomeLoss", "duration", "Net income attributable to parent"),
    _metric("operating_income", "OperatingIncomeLoss", "duration", "Operating income or loss"),
    _metric("total_assets", "Assets", "instant", "Total recognized assets"),
    _metric("total_liabilities", "Liabilities", "instant", "Total recognized liabilities"),
    _metric(
        "stockholders_equity",
        "StockholdersEquity",
        "instant",
        "Permanent equity attributable to parent, excluding noncontrolling interests",
    ),
    _metric(
        "operating_cash_flow",
        "NetCashProvidedByUsedInOperatingActivities",
        "duration",
        "Operating cash flow including discontinued operations",
    ),
)
ALIASES = {
    "assets": "total_assets",
    "liabilities": "total_liabilities",
    "net_income_loss": "net_income",
    "cash_from_operations": "operating_cash_flow",
}


def metric_definition(name: str) -> MetricDefinition | None:
    name = ALIASES.get(name, name)
    return next((metric for metric in METRICS if metric.metric_name == name), None)


def concept_kind(taxonomy: str, concept: str) -> Literal["instant", "duration"] | None:
    return next(
        (
            metric.period_kind
            for metric in METRICS
            if any(c.taxonomy == taxonomy and c.concept == concept for c in metric.concepts)
        ),
        None,
    )
