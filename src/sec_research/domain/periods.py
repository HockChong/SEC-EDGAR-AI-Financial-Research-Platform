"""Describe actual interval lengths without inventing a fiscal calendar."""

from typing import Literal

from sec_research.contracts.canonical import ReportingPeriod, ValueModel

PERIOD_POLICY: Literal["period-boundaries-1"] = "period-boundaries-1"


class PeriodAssessment(ValueModel):
    policy: Literal["period-boundaries-1"] = PERIOD_POLICY
    days: int | None
    shape: Literal[
        "instant",
        "quarter_length",
        "half_year_length",
        "nine_month_length",
        "annual_length",
        "other",
    ]


def assess_period(period: ReportingPeriod) -> PeriodAssessment:
    if period.start is None:
        return PeriodAssessment(days=None, shape="instant")
    days = (period.end - period.start).days + 1
    if 75 <= days <= 105:
        return PeriodAssessment(days=days, shape="quarter_length")
    if 165 <= days <= 200:
        return PeriodAssessment(days=days, shape="half_year_length")
    if 250 <= days <= 290:
        return PeriodAssessment(days=days, shape="nine_month_length")
    if 350 <= days <= 380:
        return PeriodAssessment(days=days, shape="annual_length")
    return PeriodAssessment(days=days, shape="other")
