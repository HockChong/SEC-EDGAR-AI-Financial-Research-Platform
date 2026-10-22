"""Preserved starter examples now run as ordinary regression tests."""

from decimal import Decimal

import pytest

from sec_research.contracts.table_normalization import NormalizedNumber, NumericContext
from sec_research.processing.table_numbers import normalize_table_number


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
            "(1,234)",
            Decimal("-1234"),
            "negative",
            False,
            False,
            "parsed",
            id="accounting-negative",
        ),
        pytest.param("0", Decimal("0"), "zero", False, False, "parsed", id="zero-is-present"),
        pytest.param("\u2014", None, None, None, True, "missing", id="dash-is-missing"),
        pytest.param(
            "15%", Decimal("15"), "positive", True, False, "parsed", id="percentage-stays-displayed"
        ),
    ],
)
def test_normalize_table_number_assignment(
    raw_text: str,
    value: Decimal | None,
    sign: str | None,
    percentage: bool | None,
    missing: bool,
    status: str,
) -> None:
    context = NumericContext(currency="USD", unit="USD", scale=Decimal("1000000"))
    result = normalize_table_number(raw_text, context=context)
    expected = NormalizedNumber.model_validate(
        {
            "raw_text": raw_text,
            "status": status,
            "value": value,
            "sign": sign,
            "currency": "USD",
            "unit": "USD",
            "scale": Decimal("1000000"),
            "percentage": percentage,
            "missing": missing,
            "warnings": (),
        }
    )
    assert result == expected
    assert isinstance(result, NormalizedNumber)
    assert result.value is None or isinstance(result.value, Decimal)
    assert context == NumericContext(currency="USD", unit="USD", scale=Decimal("1000000"))
