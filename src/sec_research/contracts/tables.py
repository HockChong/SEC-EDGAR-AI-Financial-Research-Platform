"""WP3.3 diagnostic envelope; canonical-1 storage rows remain unchanged."""

from typing import Literal, Self

from pydantic import model_validator

from sec_research.contracts.canonical import (
    ContentBlock,
    DocumentVersion,
    RecordId,
    Section,
    SourceLocator,
    StructuredTable,
    TableCell,
    Text,
    ValueModel,
    canonical_bytes,
)
from sec_research.contracts.table_normalization import NormalizedNumber

TableKind = Literal[
    "financial_statement", "financial_disclosure", "narrative", "layout", "table_of_contents"
]


class RawCell(ValueModel):
    locator: SourceLocator
    raw_text: str
    rowspan_attribute: str | None
    colspan_attribute: str | None


class CellContext(ValueModel):
    cell_id: RecordId
    column_header_ids: tuple[RecordId, ...] = ()
    row_header_ids: tuple[RecordId, ...] = ()
    period_labels: tuple[Text, ...] = ()
    normalization: NormalizedNumber


class ExtractedTable(ValueModel):
    locator: SourceLocator
    block_id: RecordId
    section_id: RecordId | None
    parent_table_path: str | None = None
    kind: TableKind
    classification_rule: Text
    title: str
    title_source: SourceLocator | None = None
    warnings: tuple[Text, ...]
    raw_cells: tuple[RawCell, ...]
    table: StructuredTable | None = None
    cells: tuple[TableCell, ...] = ()
    contexts: tuple[CellContext, ...] = ()
    grid_status: Literal["reconstructed", "quarantined"]

    @model_validator(mode="after")
    def grid(self) -> Self:
        raw_paths = [c.locator.path for c in self.raw_cells]
        if len(set(raw_paths)) != len(raw_paths) or any(
            c.locator.kind != "dom" or not c.locator.path.startswith(self.locator.path + "/")
            for c in self.raw_cells
        ):
            raise ValueError("raw cells require distinct DOM descendants of their table")
        if self.grid_status == "quarantined":
            if self.table is not None or self.cells or self.contexts or not self.warnings:
                raise ValueError("quarantined table retains raw cells but no asserted grid")
            return self
        table = self.table
        if table is None or not self.cells:
            raise ValueError("reconstructed table requires table and cells")
        if table.columns > 512 or table.rows * table.columns > 200_000:
            raise ValueError("grid exceeds supported dimensions")
        if (
            table.locator != self.locator
            or table.block_id != self.block_id
            or table.section_id != self.section_id
            or table.retrieval_text
            or table.title != self.title
        ):
            raise ValueError("table metadata mismatch or embedded retrieval text")
        by_id = {c.id: c for c in self.cells}
        if len(by_id) != len(self.cells):
            raise ValueError("duplicate cell ID")
        if len(self.contexts) != len(self.cells):
            raise ValueError("every cell requires one context")
        occupied: set[tuple[int, int]] = set()
        for cell, context in zip(self.cells, self.contexts, strict=True):
            if cell.table_id != table.id or context.cell_id != cell.id:
                raise ValueError("cell/table/context identity mismatch")
            if (
                cell.row + cell.row_span > table.rows
                or cell.column + cell.column_span > table.columns
            ):
                raise ValueError("cell span outside table")
            for row in range(cell.row, cell.row + cell.row_span):
                for column in range(cell.column, cell.column + cell.column_span):
                    if (row, column) in occupied:
                        raise ValueError("overlapping cells")
                    occupied.add((row, column))
            if cell.header_ids != context.column_header_ids + context.row_header_ids:
                raise ValueError("header context mismatch")
            if any(
                h not in by_id or not by_id[h].is_header or h == cell.id for h in cell.header_ids
            ):
                raise ValueError("invalid header reference")
            for header_id in context.column_header_ids:
                header = by_id[header_id]
                if not (
                    header.row + header.row_span <= cell.row
                    and header.column <= cell.column
                    and cell.column + cell.column_span <= header.column + header.column_span
                ):
                    raise ValueError("column header does not cover the cell")
            for header_id in context.row_header_ids:
                header = by_id[header_id]
                if not (
                    header.row <= cell.row < header.row + header.row_span
                    and header.column + header.column_span <= cell.column
                ):
                    raise ValueError("row header does not cover the cell")
            if any(
                label not in {by_id[h].display_text for h in context.column_header_ids}
                for label in context.period_labels
            ):
                raise ValueError("period labels require linked header evidence")
            if context.normalization.raw_text != cell.raw_text:
                raise ValueError("normalization must preserve raw text")
            if (
                cell.numeric_status != context.normalization.cell_status
                or cell.value != context.normalization.value
            ):
                raise ValueError("cell and normalization must agree on numeric status and value")
            if cell.footnote_markers and context.normalization.status == "parsed":
                raise ValueError("footnoted cells require numeric abstention")
        if tuple((c.locator, c.raw_text) for c in self.cells) != tuple(
            (c.locator, c.raw_text) for c in self.raw_cells
        ):
            raise ValueError("grid must preserve every source cell in source order")
        return self


class TableText(ValueModel):
    table_id: RecordId
    renderer_version: Literal["table-text-2"] = "table-text-2"
    text: str


class TableExtraction(ValueModel):
    schema_version: Literal["table-result-2"] = "table-result-2"
    extractor_version: Literal["sec-tables-2"] = "sec-tables-2"
    normalization_complete: Literal[True] = True
    document: DocumentVersion
    blocks: tuple[ContentBlock, ...]
    sections: tuple[Section, ...]
    tables: tuple[ExtractedTable, ...]
    retrieval: tuple[TableText, ...]

    @model_validator(mode="after")
    def graph(self) -> Self:
        blocks = {b.id: b for b in self.blocks}
        sections = {s.id: s for s in self.sections}
        paths = {t.locator.path for t in self.tables}
        if len(paths) != len(self.tables):
            raise ValueError("duplicate table paths")
        if any(b.document_id != self.document.id for b in self.blocks) or any(
            s.document_id != self.document.id for s in self.sections
        ):
            raise ValueError("document ownership mismatch")
        for item in self.tables:
            block = blocks.get(item.block_id)
            if block is None or block.section_id != item.section_id:
                raise ValueError("table source block mismatch")
            if item.locator.path != block.locator.path and not item.locator.path.startswith(
                block.locator.path + "/"
            ):
                raise ValueError("table must be inside its source block")
            if item.section_id is not None and item.section_id not in sections:
                raise ValueError("table section missing")
            if item.parent_table_path is not None and (
                item.parent_table_path not in paths
                or not item.locator.path.startswith(item.parent_table_path + "/")
            ):
                raise ValueError("invalid nested table parent")
            if item.table is not None and (
                item.table.document_id != self.document.id
                or item.table.pipeline_version != self.extractor_version
                or any(c.pipeline_version != self.extractor_version for c in item.cells)
            ):
                raise ValueError("table document/version mismatch")
        expected = [
            t.table.id
            for t in self.tables
            if t.table is not None and t.kind in {"financial_statement", "financial_disclosure"}
        ]
        if [t.table_id for t in self.retrieval] != expected:
            raise ValueError("retrieval must cover financial tables exactly once in source order")
        return self

    def logical_bytes(self) -> bytes:
        return canonical_bytes(self.model_dump(mode="json"))
