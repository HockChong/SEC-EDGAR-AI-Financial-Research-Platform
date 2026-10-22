"""Preserved numeric practice cases; implementation is maintained by Codex."""

from decimal import Decimal

import pytest

from exercises.wp33.normalize import normalize_financial_number
from sec_research.contracts.table_normalization import NumericContext


@pytest.mark.parametrize(
    "raw,value,sign",
    [
        (" 1,234.50 ", "1234.50", "positive"),
        ("(1,234.50)", "-1234.50", "negative"),
        ("0", "0", "zero"),
        ("-0.00", "-0.00", "zero"),
        ("123456789012345678901234567890.1234", "123456789012345678901234567890.1234", "positive"),
    ],
)
def test_exact_displayed_number(raw: str, value: str, sign: str) -> None:
    result = normalize_financial_number(raw, context=NumericContext())
    assert result.raw_text == raw
    assert result.status == "parsed" and result.value == Decimal(value)
    assert result.sign == sign and result.missing is False
    assert result.percentage is False


@pytest.mark.parametrize("raw", ["", " \u00a0 ", "—", "\u2013", "-"])
def test_missing_is_not_zero(raw: str) -> None:
    result = normalize_financial_number(raw, context=NumericContext())
    assert result.raw_text == raw
    assert result.status == "missing" and result.missing is True
    assert result.value is None and result.sign is None


def test_percent_keeps_displayed_value() -> None:
    result = normalize_financial_number("12.5%", context=NumericContext())
    assert result.value == Decimal("12.5") and result.percentage is True
    assert result.currency is None and result.scale is None


def test_explicit_context_preserved_without_multiplication() -> None:
    context = NumericContext(currency="USD", unit="currency", scale=Decimal("1000000"))
    result = normalize_financial_number("(2.5)", context=context)
    assert result.value == Decimal("-2.5")
    assert result.currency == "USD" and result.unit == "currency"
    assert result.scale == Decimal("1000000")


def test_dollar_symbol_does_not_invent_usd() -> None:
    result = normalize_financial_number("$12", context=NumericContext())
    assert result.value is None and result.currency is None
    assert result.status == "uncertain" and result.warnings == ("unsupported_numeric_format",)


@pytest.mark.parametrize("raw", ["1,23", "1.234,56", "(12", "12(a)", "--2", "\u221242"])
def test_unsupported_numeric_text_abstains(raw: str) -> None:
    result = normalize_financial_number(raw, context=NumericContext())
    assert result.raw_text == raw and result.status == "uncertain"
    assert result.value is None and result.warnings


@pytest.mark.parametrize("raw", ["Revenue", "N/A", "NaN", "Infinity"])
def test_ordinary_text(raw: str) -> None:
    result = normalize_financial_number(raw, context=NumericContext())
    assert result.status == "not_numeric" and result.value is None
