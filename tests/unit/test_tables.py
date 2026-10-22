"""Source placement, normalization integration, and integrity regressions."""

from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from sec_research.contracts.table_normalization import NormalizedNumber, NumericContext
from sec_research.contracts.tables import TableExtraction
from sec_research.processing.dom import ParseError, load_dom, resolve
from sec_research.processing.table_corpus import verify_sources
from sec_research.processing.table_grid import cell_text
from sec_research.processing.tables import extract_tables
from tests.parsing_helpers import input_html


def extract(body: str) -> TableExtraction:
    return extract_tables(*input_html(body))


def test_rowspan_colspan_and_header_associations() -> None:
    result = extract("""<table><tr><th rowspan="2">Metric</th><th colspan="2">2024</th></tr>
    <tr><th>Domestic</th><th>Foreign</th></tr>
    <tr><th scope="row">Assets</th><td>10</td><td>20</td></tr></table>""")
    item = result.tables[0]
    assert item.table is not None and (item.table.rows, item.table.columns) == (3, 3)
    domestic = next(c for c in item.cells if c.display_text == "Domestic")
    # Explicit th rows remain headers even when they contain no reporting dates.
    ten = next(c for c in item.cells if c.display_text == "10")
    by_id = {c.id: c for c in item.cells}
    assert (domestic.row, domestic.column) == (1, 1)
    assert [by_id[h].display_text for h in ten.header_ids] == ["2024", "Domestic", "Assets"]
    assert ten.value == Decimal("10") and ten.numeric_status == "parsed"


def test_rowspan_zero_stops_at_row_group() -> None:
    result = extract("""<table><tbody><tr><td rowspan="0">A</td><td>1</td></tr>
    <tr><td>2</td></tr></tbody><tbody><tr><td>B</td><td>3</td></tr></tbody></table>""")
    cells = result.tables[0].cells
    assert cells[0].row_span == 2
    assert [(c.row, c.column) for c in cells] == [(0, 0), (0, 1), (1, 1), (2, 0), (2, 1)]


@pytest.mark.parametrize(
    "attribute", ['colspan="0"', 'rowspan="no"', 'colspan="999999"', 'rowspan="4"']
)
def test_invalid_spans_preserve_raw_and_quarantine(attribute: str) -> None:
    result = extract(f"<table><tr><td {attribute}>12</td><td>34</td></tr></table>")
    item = result.tables[0]
    assert item.grid_status == "quarantined" and item.table is None and not item.cells
    assert [c.raw_text for c in item.raw_cells] == ["12", "34"]
    assert item.warnings


def test_collision_does_not_shift_amount_to_next_period() -> None:
    result = extract("""<table><tr><td>A</td><td rowspan="2">B</td><td>C</td></tr>
    <tr><td colspan="2">100</td></tr></table>""")
    item = result.tables[0]
    assert item.grid_status == "quarantined"
    assert "overlapping_span" in item.warnings
    assert item.raw_cells[-1].raw_text == "100"


def test_nested_table_independent_ownership_and_hidden_exclusion() -> None:
    result = extract(
        """<table><tr><td>Outer<table><tr><td>Inner</td><td>42</td></tr></table>end</td>
    <td><span hidden>999</span>5<sup>(a)</sup></td></tr></table>
    <div hidden><table><tr><td>SECRET</td></tr></table></div>"""
    )
    outer, inner = result.tables
    assert inner.parent_table_path == outer.locator.path
    assert outer.cells[0].raw_text == "Outer [NESTED TABLE] end"
    assert inner.cells[1].raw_text == "42"
    assert outer.cells[1].raw_text == "5(a)"
    assert outer.cells[1].footnote_markers == ("(a)",)
    assert "SECRET" not in result.model_dump_json() and "999" not in result.model_dump_json()


def test_unknown_and_ambiguous_sections_still_extract() -> None:
    result = extract_tables(
        *input_html(
            """<p>Consolidated balance sheets</p>
    <table><tr><td>Assets</td><td>20</td><td>10</td></tr></table>
    <h2>Item 3. Quantitative and Qualitative Disclosures About Market Risk.</h2>
    <table><tr><td>Interest</td><td>7</td><td>8</td></tr></table>""",
            fixture="quarter.htm",
        )
    )
    sections = {s.id: s for s in result.sections}
    assert [sections[t.section_id].classification for t in result.tables] == [
        "unclassified",
        "ambiguous",
    ]
    assert len(result.retrieval) == 2
    assert result.tables[0].kind == "financial_statement"
    assert result.tables[1].kind == "financial_disclosure"


def test_layout_heading_tables_and_toc_are_not_lost() -> None:
    result = extract("""<table><tr><td>Item 1. Business</td></tr></table>
    <table><tr><td>Table of contents</td><td>Item 1</td><td>Item 2</td></tr></table>
    <table><tr><td>Product</td><td>Description</td></tr><tr><td>A</td><td>B</td></tr></table>""")
    assert [t.kind for t in result.tables] == ["layout", "table_of_contents", "narrative"]
    assert not result.retrieval


def test_displayed_numbers_keep_unknown_currency_and_period() -> None:
    result = extract("""<table><tr><td>Revenue</td><td>$</td><td>0</td><td>—</td>
    <td></td><td>(1,234)</td><td>15%</td></tr></table>""")
    item = result.tables[0]
    assert [c.column for c in item.cells] == list(range(7))
    assert [c.display_text for c in item.cells] == ["Revenue", "$", "0", "—", "", "(1,234)", "15%"]
    assert item.cells[4].numeric_status == "empty"
    assert [c.normalization.status for c in item.contexts] == [
        "not_numeric",
        "not_numeric",
        "parsed",
        "missing",
        "missing",
        "parsed",
        "parsed",
    ]
    assert [c.value for c in item.cells] == [
        None,
        None,
        Decimal("0"),
        None,
        None,
        Decimal("-1234"),
        Decimal("15"),
    ]
    for context in item.contexts:
        number = context.normalization
        assert number.currency is None and number.unit is None and number.scale is None
        assert not context.period_labels
    assert "[unknown]" in result.retrieval[0].text


def test_numeric_footnotes_do_not_manufacture_amounts() -> None:
    result = extract("<table><tr><td>12<sup>1</sup></td><td>42(a)</td></tr></table>")
    item = result.tables[0]
    assert item.cells[0].raw_text == "121" and item.cells[0].footnote_markers == ("1",)
    assert all(c.value is None and c.numeric_status == "uncertain" for c in item.cells)
    assert item.contexts[0].normalization.warnings == ("footnote_numeric_ambiguity",)


def test_numeric_envelope_rejects_conflicting_values() -> None:
    result = extract("<table><tr><td>42</td></tr></table>")
    payload = result.model_dump(mode="json")
    payload["tables"][0]["contexts"][0]["normalization"]["value"] = "43"
    with pytest.raises(ValidationError, match="must agree"):
        TableExtraction.model_validate(payload)


def test_provenance_roundtrip_replay_and_raw_cell_resolution() -> None:
    body = (Path(__file__).parents[1] / "fixtures/tables/multi-period.htm").read_bytes()
    fetch, data = input_html(body, fixture="quarter.htm")
    result = extract_tables(fetch, data)
    assert TableExtraction.model_validate_json(result.model_dump_json()) == result
    assert result.logical_bytes() == extract_tables(fetch, data).logical_bytes()
    root = load_dom(data).root
    for item in result.tables:
        assert resolve(root, item.locator.path).tag == "table"
        for cell in item.raw_cells:
            assert cell_text(resolve(root, cell.locator.path)) == cell.raw_text
    assert result.document.source.sha256 == fetch.sha256
    with pytest.raises(ParseError, match="source_integrity"):
        extract_tables(fetch, data + b" ")


def test_envelope_rejects_foreign_document_and_corrupt_header_graph() -> None:
    result = extract("<table><tr><th>2025</th></tr><tr><td>12</td></tr></table>")
    payload = result.model_dump(mode="json")
    payload["tables"][0]["contexts"][1]["column_header_ids"] = []
    with pytest.raises(ValidationError, match="header context mismatch"):
        TableExtraction.model_validate(payload)
    payload = result.model_dump(mode="json")
    payload["document"] = extract("<table><tr><td>other</td></tr></table>").document.model_dump(
        mode="json"
    )
    with pytest.raises(ValidationError, match="document ownership mismatch"):
        TableExtraction.model_validate(payload)


@pytest.mark.parametrize("value", [1.5, "NaN", "Infinity"])
def test_numeric_contract_forbids_float_and_nonfinite(value: object) -> None:
    with pytest.raises(ValidationError):
        NormalizedNumber.model_validate(
            {
                "raw_text": "1.5",
                "status": "parsed",
                "value": value,
                "sign": "positive",
                "missing": False,
                "percentage": False,
            }
        )


def test_numeric_contract_rejects_sign_and_missing_contradictions() -> None:
    with pytest.raises(ValidationError, match="consistent sign"):
        NormalizedNumber(
            raw_text="(1)",
            status="parsed",
            value=Decimal("-1"),
            sign="positive",
            missing=False,
            percentage=False,
        )
    with pytest.raises(ValidationError, match="explicit missing"):
        NormalizedNumber(raw_text="—", status="missing", missing=False)
    with pytest.raises(ValidationError):
        NumericContext(scale=Decimal("0"))


def test_source_audit_rejects_different_bytes_and_span_metadata() -> None:
    fetch, body = input_html('<table><tr><td colspan="0">12</td></tr></table>')
    result = extract_tables(fetch, body)
    with pytest.raises(ValueError, match="source integrity mismatch"):
        verify_sources(result, body + b" ")
    item = result.tables[0]
    raw = item.raw_cells[0].model_copy(update={"colspan_attribute": "1"})
    changed = item.model_copy(update={"raw_cells": (raw,)})
    with pytest.raises(ValueError, match="span source mismatch"):
        verify_sources(result.model_copy(update={"tables": (changed,)}), body)


def test_ragged_rows_warn_without_inventing_cells() -> None:
    result = extract("<table><tr><td>A</td><td>B</td></tr><tr><td>C</td></tr></table>")
    item = result.tables[0]
    assert "ragged_rows" in item.warnings
    assert len(item.cells) == 3 and item.table is not None
    assert (item.table.rows, item.table.columns) == (2, 2)


def test_cells_outside_rows_and_empty_tables_are_retained() -> None:
    result = extract("<table><td>orphan</td></table><table></table>")
    assert [t.grid_status for t in result.tables] == ["quarantined", "quarantined"]
    assert result.tables[0].raw_cells[0].raw_text == "orphan"
    assert "empty_table" in result.tables[1].warnings


@pytest.mark.parametrize("title", ["INCOME STATEMENTS", "CASH FLOWS STATEMENTS"])
def test_statement_name_variants(title: str) -> None:
    result = extract(f"<p>{title}</p><table><tr><td>Cash</td><td>10</td><td>20</td></tr></table>")
    assert result.tables[0].title == title
    assert result.tables[0].kind == "financial_statement"


def test_prose_mention_is_not_a_statement_title() -> None:
    result = extract(
        "<p>Refer to the Consolidated Balance Sheets for details.</p>"
        "<table><tr><td>Assets</td><td>10</td><td>20</td></tr></table>"
    )
    assert result.tables[0].title == ""
    assert result.tables[0].kind == "financial_disclosure"
