"""Compatibility import for practice tests; edit processing/table_numbers.py only."""

from sec_research.processing.table_numbers import (
    normalize_table_number as normalize_financial_number,
)

__all__ = ["normalize_financial_number"]
