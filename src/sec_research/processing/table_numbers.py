"""Conservative, exact parsing of displayed table numbers."""

import re
from decimal import Decimal

from sec_research.contracts.table_normalization import NormalizedNumber, NumericContext

_MAGNITUDE = r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?"
_NUMBER = re.compile(rf"(?P<signed>[+-]?{_MAGNITUDE})|\((?P<accounting>{_MAGNITUDE})\)")


def normalize_table_number(raw_text: str, *, context: NumericContext) -> NormalizedNumber:
    """Interpret one displayed number under the bounded table-numeric-1 policy.

    Preserve raw_text exactly. Work on a stripped copy. Accept ASCII digits,
    an optional leading + or -, correctly grouped thousands commas, an optional
    decimal fraction, accounting parentheses for negatives, and a trailing %.
    Parentheses and a leading sign cannot be combined. Use Decimal, never float.

    Parsed results carry the signed DISPLAYED value (no scale multiplication or
    percent division), its sign, missing=False, and a percentage boolean.
    Copy currency/unit/scale only from context; never guess them from a symbol.

    Empty/whitespace-only text and a single -, en dash, or em dash are missing:
    value/sign=None, missing=True, percentage=None. Plain nonnumeric labels are
    not_numeric with value/sign=None, missing=False, percentage=None.
    Other unsupported text containing digits is uncertain with the same empty
    value fields and warnings=("unsupported_numeric_format",). Never discard
    footnote markers, currency symbols, bad comma grouping, or conflicting signs
    to manufacture a value. Non-uncertain results have warnings=().

    All results retain the supplied context and the default policy_version.
    See docs/table-extraction.md for integration limits.
    """
    metadata = context.model_dump()
    text = raw_text.strip()
    if text in {"", "-", "\u2013", "\u2014"}:
        return NormalizedNumber(raw_text=raw_text, status="missing", missing=True, **metadata)
    percentage = text.endswith("%")
    match = _NUMBER.fullmatch(text[:-1] if percentage else text)
    if match is None:
        numeric = any(character.isdigit() for character in text)
        return NormalizedNumber(
            raw_text=raw_text,
            status="uncertain" if numeric else "not_numeric",
            missing=False,
            warnings=("unsupported_numeric_format",) if numeric else (),
            **metadata,
        )
    # Construct the sign lexically: Decimal unary minus can round to ambient precision.
    token = match["signed"] or "-" + match["accounting"]
    value = Decimal(token.replace(",", ""))
    return NormalizedNumber(
        raw_text=raw_text,
        status="parsed",
        value=value,
        sign="negative" if value < 0 else "positive" if value > 0 else "zero",
        missing=False,
        percentage=percentage,
        **metadata,
    )
