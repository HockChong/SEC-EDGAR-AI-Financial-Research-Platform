"""Financial lexical edge cases and boundary validation."""

from decimal import Decimal, localcontext

import pytest
from pydantic import ValidationError

from sec_research.contracts.table_normalization import NormalizedNumber, NumericContext
from sec_research.processing.table_numbers import normalize_table_number


@pytest.mark.parametrize(
    "raw",
    [
        "1,23",
        "1234,567",
        "1,,000",
        "1.234,56",
        "1 234",
        "1\u00a0234",
        "1e3",
        "(12",
        "12)",
        "(-12)",
        "(+12)",
        "--2",
        "+-2",
        "12(a)",
        "$12",
        "\u221242",
        "12%%",
        "12 %",
        ".5",
        "5.",
        "(12%)",
        "\uff11\uff12",
        "١٢",
        "2026-06-30",
    ],
)
def test_unsupported_numeric_formats_abstain(raw: str) -> None:
    result = normalize_table_number(raw, context=NumericContext())
    assert result.raw_text == raw and result.status == "uncertain"
    assert result.value is None and result.sign is None and result.percentage is None
    assert result.missing is False and result.warnings == ("unsupported_numeric_format",)


@pytest.mark.parametrize("raw", ["Revenue", "N/A", "NaN", "Infinity", "-Infinity", "$", "%"])
def test_labels_are_not_numbers(raw: str) -> None:
    result = normalize_table_number(raw, context=NumericContext())
    assert result.status == "not_numeric" and result.missing is False and not result.warnings


@pytest.mark.parametrize("raw", ["", " \u00a0 ", "-", "\u2013", "\u2014"])
def test_missing_keeps_source_and_context(raw: str) -> None:
    result = normalize_table_number(
        raw, context=NumericContext(currency="EUR", scale=Decimal("1000"))
    )
    assert result.status == "missing" and result.missing is True and result.raw_text == raw
    assert result.currency == "EUR" and result.scale == Decimal("1000")
    assert result.value is None and result.percentage is None


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("+1,234.50", "1234.50"),
        ("(123456789012345678901234567890.1234)", "-123456789012345678901234567890.1234"),
        ("-0.00", "-0.00"),
        ("(12.5)%", "-12.5"),
        ("\t12.50%\n", "12.50"),
    ],
)
def test_exact_values_independent_of_decimal_context(raw: str, expected: str) -> None:
    with localcontext() as arithmetic:
        arithmetic.prec = 3
        result = normalize_table_number(raw, context=NumericContext())
    assert result.value is not None and result.value.as_tuple() == Decimal(expected).as_tuple()
    assert result.percentage is raw.strip().endswith("%")
    assert NormalizedNumber.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "missing", "missing": True, "percentage": True},
        {"status": "not_numeric"},
        {"status": "uncertain", "missing": False},
        {"status": "pending", "warnings": ["old_gate"]},
        {"status": "parsed", "value": "12", "sign": "positive", "missing": False},
    ],
)
def test_invalid_result_states_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        NormalizedNumber.model_validate({"raw_text": "12", **payload})


@pytest.mark.parametrize(
    "context", [{"scale": "NaN"}, {"scale": "-1"}, {"scale": 1.2}, {"currency": "$"}]
)
def test_invalid_context_rejected(context: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        NumericContext.model_validate(context)
