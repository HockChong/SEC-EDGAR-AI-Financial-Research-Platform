"""Source-audit rejection paths, independent of the learner's normalization function."""

import pytest

from sec_research.processing.table_corpus import verify_sources
from sec_research.processing.tables import extract_tables
from tests.parsing_helpers import input_html


def test_source_audit_covers_nested_and_quarantined_cells() -> None:
    fetch, body = input_html(
        "<table><tr><td>Outer<table><tr><td>Inner</td></tr></table></td></tr></table>"
        '<table><tr><td colspan="0">Unsupported grid</td></tr></table>'
        "<table hidden><tr><td>Hidden</td></tr></table>"
    )
    result = extract_tables(fetch, body)
    assert len(result.tables) == 3
    assert result.tables[-1].grid_status == "quarantined"
    assert verify_sources(result, body) == 3


def test_source_audit_rejects_omitted_table() -> None:
    fetch, body = input_html("<table><tr><td>A</td></tr></table>")
    result = extract_tables(fetch, body)
    # model_copy deliberately bypasses validation to simulate a corrupt result.
    corrupt = result.model_copy(update={"tables": (), "retrieval": ()})
    with pytest.raises(ValueError, match="table enumeration mismatch"):
        verify_sources(corrupt, body)


def test_source_audit_rejects_omitted_cell_in_quarantine() -> None:
    fetch, body = input_html('<table><tr><td colspan="0">A</td><td>B</td></tr></table>')
    result = extract_tables(fetch, body)
    table = result.tables[0].model_copy(update={"raw_cells": result.tables[0].raw_cells[:1]})
    corrupt = result.model_copy(update={"tables": (table,)})
    with pytest.raises(ValueError, match="cell enumeration mismatch"):
        verify_sources(corrupt, body)


def test_source_audit_rejects_altered_lexical_value() -> None:
    fetch, body = input_html('<table><tr><td colspan="0">(1,234)</td></tr></table>')
    result = extract_tables(fetch, body)
    cell = result.tables[0].raw_cells[0].model_copy(update={"raw_text": "1234"})
    table = result.tables[0].model_copy(update={"raw_cells": (cell,)})
    corrupt = result.model_copy(update={"tables": (table,)})
    with pytest.raises(ValueError, match="cell lexical source mismatch"):
        verify_sources(corrupt, body)
