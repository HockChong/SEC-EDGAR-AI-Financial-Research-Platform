"""Synthetic multi-period associations must not cross duration or year groups."""

from decimal import Decimal
from pathlib import Path

from sec_research.processing.tables import extract_tables
from tests.parsing_helpers import input_html


def test_multi_period_header_associations() -> None:
    fixture = Path(__file__).parents[1] / "fixtures/tables/multi-period.htm"
    result = extract_tables(*input_html(fixture.read_bytes(), fixture="quarter.htm"))
    item = result.tables[0]
    assert item.table is not None and (item.table.rows, item.table.columns) == (5, 5)
    cells = {cell.id: cell for cell in item.cells}
    contexts = {context.cell_id: context for context in item.contexts}
    june_ids = []
    for column, raw, group, year in (
        (1, "1,234", "Three months ended", "2026"),
        (2, "1,100", "Three months ended", "2025"),
        (3, "2,400", "Six months ended", "2026"),
        (4, "2,000", "Six months ended", "2025"),
    ):
        cell = next(c for c in item.cells if (c.row, c.column) == (3, column))
        assert cell.id is not None
        context = contexts[cell.id]
        assert cell.raw_text == raw and cell.value == Decimal(raw.replace(",", ""))
        assert [cells[h].display_text for h in context.column_header_ids] == [
            group,
            "June 30",
            year,
        ]
        assert [cells[h].display_text for h in context.row_header_ids] == ["Revenue"]
        assert cell.header_ids == context.column_header_ids + context.row_header_ids
        assert context.period_labels == (group, "June 30", year)
        assert context.normalization.scale is None  # Mixed-unit heading is only a raw hint.
        june_ids.append(context.column_header_ids[1])
    assert june_ids[0] == june_ids[1] and june_ids[2] == june_ids[3]
    assert june_ids[0] != june_ids[2]
    assert all(not c.header_ids for c in item.cells if c.is_header)


def test_amount_spanning_period_groups_has_no_invented_period() -> None:
    body = """<table><tr><th>Metric</th><th>2026</th><th>2025</th></tr>
    <tr><th scope="row">Revenue</th><td colspan="2">42</td></tr></table>"""
    item = extract_tables(*input_html(body)).tables[0]
    context = item.contexts[-1]
    assert context.column_header_ids == () and context.period_labels == ()
    assert len(context.row_header_ids) == 1
