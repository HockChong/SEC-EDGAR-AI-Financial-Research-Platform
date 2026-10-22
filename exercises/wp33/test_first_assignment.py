"""Preserved starter examples for displayed-number normalization."""

from decimal import Decimal

import pytest

from exercises.wp33.normalize import normalize_financial_number
from sec_research.contracts.table_normalization import NormalizedNumber, NumericContext


@pytest.mark.parametrize(
    ("raw_text", "value", "sign", "percentage", "missing", "status"),
    [
        pytest.param(
            " 1,234.50 ",
            Decimal("1234.50"),
            "positive",
            False,
            False,
            "parsed",
            id="commas-whitespace-and-context",
        ),
        pytest.param(
            "(1,234.50)",
            Decimal("-1234.50"),
            "negative",
            False,
            False,
            "parsed",
            id="accounting-negative",
        ),
        pytest.param("0", Decimal("0"), "zero", False, False, "parsed", id="zero-is-present"),
        pytest.param("\u2014", None, None, None, True, "missing", id="dash-is-missing"),
        pytest.param(
            "12.5%",
            Decimal("12.5"),
            "positive",
            True,
            False,
            "parsed",
            id="percentage-stays-displayed",
        ),
    ],
)
def test_first_assignment(
    raw_text: str,
    value: Decimal | None,
    sign: str | None,
    percentage: bool | None,
    missing: bool,
    status: str,
) -> None:
    context = NumericContext(currency="USD", unit="currency", scale=Decimal("1000000"))
    result = normalize_financial_number(raw_text, context=context)
    expected = NormalizedNumber.model_validate(
        {
            "raw_text": raw_text,
            "status": status,
            "value": value,
            "sign": sign,
            "currency": "USD",
            "unit": "currency",
            "scale": Decimal("1000000"),
            "percentage": percentage,
            "missing": missing,
            "warnings": (),
        }
    )
    assert result == expected
    assert isinstance(result, NormalizedNumber)
    assert result.value is None or isinstance(result.value, Decimal)
