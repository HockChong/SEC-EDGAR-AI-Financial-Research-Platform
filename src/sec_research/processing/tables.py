"""Deterministic source-linked tables and conservative displayed-number normalization."""

import re

from lxml import etree

from sec_research.contracts.canonical import (
    ContentBlock,
    SourceLocator,
    StructuredTable,
    TableCell,
)
from sec_research.contracts.table_normalization import NormalizedNumber, NumericContext
from sec_research.contracts.tables import (
    CellContext,
    ExtractedTable,
    TableExtraction,
    TableKind,
    TableText,
)
from sec_research.ingestion.ports import Fetch
from sec_research.processing.blocks import normalize, visible_text
from sec_research.processing.dom import load_dom, locator, tag
from sec_research.processing.html import parse_html, record_id
from sec_research.processing.table_grid import (
    Grid,
    Placement,
    display,
    nearest,
    reconstruct,
    visible,
)
from sec_research.processing.table_numbers import normalize_table_number

EXTRACTOR_VERSION = "sec-tables-2"
STATEMENT = re.compile(
    r"(?:consolidated\s+)?(?:balance\s+sheets?|statements?\s+of\s+"
    r"(?:income|operations|earnings|cash\s+flows|financial\s+position|comprehensive\s+income|"
    r"changes\s+in\s+.*equity|stockholders.?\s+equity|shareholders.?\s+equity))|"
    r"(?:income|cash\s+flows?|operations|earnings)\s+statements?",
    re.I,
)
PERIOD = re.compile(
    r"\b(?:19|20)\d{2}\b|\b(?:months?|years?|quarters?|weeks?)\s+ended\b|"
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b",
    re.I,
)
UNIT = re.compile(
    r"\b(?:in\s+(?:millions|thousands|billions)|per\s+share|percent|USD|EUR|GBP|"
    r"U\.?S\.?\s+dollars|shares\s+in\s+\w+)\b",
    re.I,
)
FINANCE = re.compile(
    r"\b(?:revenue|sales|assets|liabilities|equity|income|cash|earnings|debt|"
    r"expense|capital|interest|shares|tax|dividends|securities|loans)\b",
    re.I,
)
# This recognizes display-shaped tokens for STRUCTURAL classification only. No Decimal conversion.
AMOUNT_SHAPE = re.compile(r"^[\s$€£¥()+\-\u2212\d,.%]+$")


def amount_shaped(text: str) -> bool:
    return bool(re.search(r"\d", text) and AMOUNT_SHAPE.fullmatch(text))


def statement_title(text: str) -> bool:
    prefix_removed = re.sub(
        r"^(?:(?:condensed|consolidated|combined|unaudited|audited)\s+)+",
        "",
        text,
        flags=re.I,
    )
    return len(text) <= 180 and STATEMENT.match(prefix_removed) is not None


def classify_table(node: etree._Element, grid: Grid, title: str) -> tuple[TableKind, str]:
    texts = [normalize(c.raw_text) for c in grid.raw]
    joined = " ".join(texts)
    links = [a for a in node.iter("a") if a.get("href", "").startswith("#")]
    if re.search(r"table\s+of\s+contents", joined, re.I) or (
        len(links) >= 3 and len(re.findall(r"\bitem\s+\d", joined, re.I)) >= 2
    ):
        return "table_of_contents", "toc_labels_and_links"
    numeric = sum(amount_shaped(t) for t in texts)
    if statement_title(title) and numeric >= 2:
        return "financial_statement", "statement_title_and_numeric_cells"
    if numeric >= 2 and FINANCE.search(joined):
        return "financial_disclosure", "financial_vocabulary_and_numeric_cells"
    if len([t for t in texts if t]) <= 2 or not grid.raw:
        return "layout", "few_nonempty_cells"
    return "narrative", "fallback_narrative_uncertain"


def title_for(
    node: etree._Element, owner: ContentBlock, blocks: tuple[ContentBlock, ...], grid: Grid
) -> tuple[str, SourceLocator | None]:
    caption = next((n for n in node if tag(n) == "caption" and visible(n)), None)
    if caption is not None:
        return normalize(visible_text(caption)), SourceLocator(kind="dom", path=locator(caption))
    for cell in grid.raw[:12]:
        text = normalize(cell.raw_text)
        if statement_title(text):
            return text, cell.locator
    # Stop at another table; avoid inheriting a prior financial statement's title.
    for block in reversed(blocks[max(0, owner.ordinal - 4) : owner.ordinal]):
        if block.kind == "table":
            break
        if statement_title(block.text):
            return block.text, SourceLocator(kind="dom", path=block.locator.path)
    return "", None


def header_roles(grid: Grid) -> tuple[set[int], set[int]]:
    """Conservative leading-header detection; source columns, including spacers, stay intact."""
    column_headers: set[int] = set()
    row_headers: set[int] = set()
    body_started = False
    for row in range(grid.rows):
        indices = [i for i, p in enumerate(grid.placed) if p.row == row]
        meaningful = [i for i in indices if display(grid.placed[i])]
        has_period = any(PERIOD.search(display(grid.placed[i])) for i in meaningful)
        numeric = [
            i
            for i in meaningful
            if amount_shaped(display(grid.placed[i]))
            and not re.fullmatch(r"(?:19|20)\d{2}", display(grid.placed[i]))
        ]
        all_th = bool(meaningful) and all(tag(grid.placed[i].node) == "th" for i in meaningful)
        if not body_started and (all_th or (has_period and not numeric)):
            column_headers.update(meaningful)
            continue
        if numeric:
            body_started = True
        for i in meaningful:
            p = grid.placed[i]
            if p.node.get("scope", "").lower() == "col":
                column_headers.add(i)
            elif p.node.get("scope", "").lower() == "row" or (
                numeric
                and i < numeric[0]
                and not amount_shaped(display(p))
                and display(p) not in {"$", "€", "£", "¥", "(", ")", "\u2212", "-"}
            ):
                row_headers.add(i)
    return column_headers, row_headers


def footnotes(p: Placement) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            normalize(visible_text(n))
            for n in p.node.iter()
            if visible(n)
            and nearest(n, "table") is nearest(p.node, "table")
            and (tag(n) == "sup" or (tag(n) == "a" and n.get("href", "").startswith("#")))
            and normalize(visible_text(n))
        )
    )


def build_cells(
    table: StructuredTable, grid: Grid
) -> tuple[tuple[TableCell, ...], tuple[CellContext, ...]]:
    columns, rows = header_roles(grid)
    base: list[TableCell] = []
    numbers: list[NormalizedNumber] = []
    for i, p in enumerate(grid.placed):
        text = display(p)
        markers = footnotes(p)
        number = normalize_table_number(p.raw.raw_text, context=NumericContext())
        if markers and number.status == "parsed":
            # E.g. 12<sup>1</sup> has lexical text 121, not an asserted amount of 121.
            number = NormalizedNumber(
                raw_text=p.raw.raw_text,
                status="uncertain",
                missing=False,
                warnings=("footnote_numeric_ambiguity",),
            )
        numbers.append(number)
        base.append(
            TableCell(
                pipeline_version=EXTRACTOR_VERSION,
                table_id=record_id(table),
                row=p.row,
                column=p.column,
                row_span=p.row_span,
                column_span=p.column_span,
                is_header=i in columns | rows,
                raw_text=p.raw.raw_text,
                display_text=text,
                numeric_status=number.cell_status,
                value=number.value,
                footnote_markers=markers,
                locator=p.raw.locator,
            )
        )
    cells: list[TableCell] = []
    contexts: list[CellContext] = []
    by_id = {record_id(c): c for c in base}
    for cell, number in zip(base, numbers, strict=True):
        # Header cells have no outgoing header IDs, avoiding cyclic content identities.
        col_refs = tuple(
            record_id(base[j])
            for j in sorted(columns)
            if not cell.is_header
            and base[j].row + base[j].row_span <= cell.row
            and base[j].column <= cell.column
            and cell.column + cell.column_span <= base[j].column + base[j].column_span
        )
        row_refs = tuple(
            record_id(base[j])
            for j in sorted(rows)
            if not cell.is_header
            and base[j].row <= cell.row < base[j].row + base[j].row_span
            and base[j].column + base[j].column_span <= cell.column
        )
        periods = tuple(
            by_id[h].display_text for h in col_refs if PERIOD.search(by_id[h].display_text)
        )
        updated = TableCell.model_validate(
            {
                **cell.model_dump(exclude={"id"}),
                "header_ids": col_refs + row_refs,
            }
        )
        cells.append(updated)
        contexts.append(
            CellContext(
                cell_id=record_id(updated),
                column_header_ids=col_refs,
                row_header_ids=row_refs,
                period_labels=periods,
                normalization=number,
            )
        )
    return tuple(cells), tuple(contexts)


def render_table(
    item: ExtractedTable, document_source: str, cik: str, accession: str, form: str
) -> TableText:
    assert item.table is not None
    by_id = {record_id(c): c for c in item.cells}
    lines = [
        f"Company CIK: {cik}; accession: {accession}; form: {form}",
        f"Title: {item.title or '[unknown]'}",
        f"Source: {document_source}; DOM: {item.locator.path}; table: {item.table.id}",
        "Values retain raw source text; displayed-number parsing is not financial verification.",
        "Unit/scale labels: " + (" | ".join(item.table.unit_hints) or "[unknown]"),
    ]
    for cell, context in zip(item.cells, item.contexts, strict=True):
        if not cell.display_text:
            continue
        headers = " > ".join(by_id[h].display_text for h in cell.header_ids) or "[unresolved]"
        periods = " > ".join(context.period_labels) or "[unknown]"
        lines.append(
            f"r{cell.row} c{cell.column} span={cell.row_span}x{cell.column_span}; "
            f"headers={headers}; periods={periods}; raw={cell.display_text!r}; "
            f"cell={cell.id}; DOM={cell.locator.path}"
        )
    return TableText(table_id=record_id(item.table), text="\n".join(lines))


def extract_tables(fetch: Fetch, body: bytes) -> TableExtraction:
    """Pure offline entry point; validates source bytes through the existing WP3.2 parser."""
    parsed = parse_html(fetch, body)
    dom = load_dom(body)
    block_paths = {b.locator.path: b for b in parsed.blocks}
    items: list[ExtractedTable] = []
    retrieval: list[TableText] = []
    for node in dom.root.iter("table"):
        if not visible(node):
            continue
        path = locator(node)
        parent = nearest(node, "table")
        owner_node = node
        while (ancestor := nearest(owner_node, "table")) is not None:
            owner_node = ancestor
        owner = block_paths.get(locator(owner_node))
        if owner is None:
            raise ValueError("visible table has no WP3.2 source block")
        grid = reconstruct(node)
        title, title_source = title_for(node, owner, parsed.blocks, grid)
        kind, rule = classify_table(node, grid, title)
        warnings = [*grid.warnings, "classification_heuristic", "financial_context_unverified"]
        if dom.warnings:
            warnings.extend(dom.warnings)
        if parent is not None or any(tag(n) == "table" for n in node.iterdescendants()):
            warnings.append("nested_table_separate_ownership")
        table = None
        cells: tuple[TableCell, ...] = ()
        contexts: tuple[CellContext, ...] = ()
        if grid.placed:
            hints = tuple(
                dict.fromkeys(
                    normalize(c.raw_text)
                    for c in grid.raw
                    if UNIT.search(c.raw_text) and len(normalize(c.raw_text)) <= 240
                )
            )
            table = StructuredTable(
                pipeline_version=EXTRACTOR_VERSION,
                document_id=record_id(parsed.document),
                section_id=owner.section_id,
                block_id=record_id(owner),
                locator=SourceLocator(kind="dom", path=path),
                rows=grid.rows,
                columns=grid.columns,
                title=title,
                unit_hints=hints,
                retrieval_text="",
                quality="warning",
            )
            cells, contexts = build_cells(table, grid)
            if not any(c.column_header_ids for c in contexts):
                warnings.append("column_headers_unresolved")
            if any(
                amount_shaped(c.display_text) and not ctx.period_labels
                for c, ctx in zip(cells, contexts, strict=True)
                if not c.is_header
            ):
                warnings.append("numeric_period_unresolved")
        item = ExtractedTable(
            locator=SourceLocator(kind="dom", path=path),
            block_id=record_id(owner),
            section_id=owner.section_id,
            parent_table_path=locator(parent) if parent is not None else None,
            kind=kind,
            classification_rule=rule,
            title=title,
            title_source=title_source,
            warnings=tuple(dict.fromkeys(warnings)),
            raw_cells=grid.raw,
            table=table,
            cells=cells,
            contexts=contexts,
            grid_status="reconstructed" if table is not None else "quarantined",
        )
        items.append(item)
        if table is not None and kind in {"financial_statement", "financial_disclosure"}:
            filing = parsed.filing.filing
            retrieval.append(
                render_table(
                    item,
                    parsed.document.source.source.url,
                    filing.cik,
                    filing.accession,
                    filing.form,
                )
            )
    return TableExtraction(
        document=parsed.document,
        blocks=parsed.blocks,
        sections=parsed.sections,
        tables=tuple(items),
        retrieval=tuple(retrieval),
    )
