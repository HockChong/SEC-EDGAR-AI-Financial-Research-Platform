"""Bounded source-cell placement; ambiguous spans quarantine, never move amounts."""

from dataclasses import dataclass

from lxml import etree

from sec_research.contracts.canonical import SourceLocator
from sec_research.contracts.tables import RawCell
from sec_research.processing.blocks import hidden, normalize
from sec_research.processing.dom import locator, tag

MAX_COLUMNS = 512
MAX_SLOTS = 200_000


def visible(node: etree._Element) -> bool:
    return not hidden(node) and not any(hidden(a) for a in node.iterancestors())


def nearest(node: etree._Element, name: str) -> etree._Element | None:
    return next((a for a in node.iterancestors() if tag(a) == name), None)


def cell_text(node: etree._Element) -> str:
    """Visible lexical text, retaining whitespace and separating nested table ownership."""
    if hidden(node):
        return ""
    if tag(node) == "table":
        return " [NESTED TABLE] "
    parts = [node.text or ""]
    for child in node:
        parts.append(" " if tag(child) == "br" else cell_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


@dataclass(frozen=True)
class Placement:
    node: etree._Element
    raw: RawCell
    row: int
    column: int
    row_span: int
    column_span: int


@dataclass(frozen=True)
class Grid:
    raw: tuple[RawCell, ...]
    placed: tuple[Placement, ...]
    rows: int
    columns: int
    warnings: tuple[str, ...]


def reconstruct(table: etree._Element) -> Grid:
    rows = [n for n in table.iter("tr") if nearest(n, "table") is table and visible(n)]
    nodes = [
        n
        for n in table.iter()
        if tag(n) in {"td", "th"} and nearest(n, "table") is table and visible(n)
    ]
    raw = tuple(
        RawCell(
            locator=SourceLocator(kind="dom", path=locator(n)),
            raw_text=cell_text(n),
            rowspan_attribute=n.get("rowspan"),
            colspan_attribute=n.get("colspan"),
        )
        for n in nodes
    )

    def failed(code: str) -> Grid:
        return Grid(raw, (), len(rows), 0, (code,))

    if not rows or not nodes:
        return failed("empty_table")
    row_index = {n: i for i, n in enumerate(rows)}
    if any(nearest(n, "tr") not in row_index for n in nodes):
        return failed("cell_outside_row")
    occupied: set[tuple[int, int]] = set()
    placed: list[Placement] = []
    cursor: dict[int, int] = {}
    width = 0
    for node, source in zip(nodes, raw, strict=True):
        owner = nearest(node, "tr")
        assert owner is not None
        row = row_index[owner]
        group = owner.getparent()
        # HTML rowspan=0 extends only through the current row group.
        group_end = row + 1
        while group_end < len(rows) and rows[group_end].getparent() is group:
            group_end += 1
        attributes = (node.get("rowspan", "1").strip(), node.get("colspan", "1").strip())
        if any(not a.isascii() or not a.isdecimal() or len(a) > 6 for a in attributes):
            return failed("invalid_span")
        rs, cs = map(int, attributes)
        if rs == 0:
            rs = group_end - row
        if cs < 1 or cs > MAX_COLUMNS or rs > len(rows) or row + rs > group_end:
            return failed("span_outside_group_or_limit")
        column = cursor.get(row, 0)
        while (row, column) in occupied:
            column += 1
        if column + cs > MAX_COLUMNS or rs * cs + len(occupied) > MAX_SLOTS:
            return failed("grid_resource_limit")
        slots = {(r, c) for r in range(row, row + rs) for c in range(column, column + cs)}
        if slots & occupied:
            return failed("overlapping_span")
        occupied.update(slots)
        placed.append(Placement(node, source, row, column, rs, cs))
        cursor[row] = column + cs
        width = max(width, column + cs)
    if len(rows) * width > MAX_SLOTS:
        return failed("grid_resource_limit")
    warnings = ("ragged_rows",) if len(occupied) != len(rows) * width else ()
    return Grid(raw, tuple(placed), len(rows), width, warnings)


def display(placement: Placement) -> str:
    return normalize(placement.raw.raw_text)
