"""Reading-order text ownership. Each visible text node is visited exactly once."""

import re
from dataclasses import dataclass, replace
from typing import Literal

from lxml import etree

from sec_research.processing.dom import ParseError, locator, tag

BlockKind = Literal["heading", "paragraph", "list", "table", "footnote", "other"]
BOUNDARIES = {
    "html",
    "body",
    "div",
    "p",
    "section",
    "article",
    "header",
    "footer",
    "nav",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "table",
    "blockquote",
    "pre",
}
SKIP = {
    "head",
    "script",
    "style",
    "noscript",
    "template",
    "ix:hidden",
    "ix:header",
    "ix:resources",
    "ix:references",
    "xbrli:context",
    "xbrli:unit",
}
LABEL = re.compile(r"^(?:item\s+\d{1,2}[a-c]?\b|part\s+[iv]+\b)", re.I)
MAX_BLOCKS = 100_000


@dataclass(frozen=True)
class DraftBlock:
    kind: BlockKind
    text: str
    path: str
    heading: bool = False
    toc: bool = False


def normalize(text: str) -> str:
    return " ".join(text.replace("\u200b", "").replace("\ufeff", "").split())


def hidden(node: etree._Element) -> bool:
    style = re.sub(r"\s+", "", node.get("style", "").lower())
    return (
        tag(node) in SKIP
        or not tag(node)
        or node.get("hidden") is not None
        or node.get("aria-hidden", "").lower() == "true"
        or "display:none" in style
        or "visibility:hidden" in style
    )


def visible_text(node: etree._Element) -> str:
    if hidden(node):
        return ""
    parts = [node.text or ""]
    for child in node:
        parts.append(" " if tag(child) == "br" else visible_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


def extract_blocks(root: etree._Element) -> tuple[DraftBlock, ...]:
    blocks: list[DraftBlock] = []

    def append(block: DraftBlock) -> None:
        blocks.append(block)
        if len(blocks) > MAX_BLOCKS:
            raise ParseError("block_resource_limit")

    def visit(node: etree._Element, toc: bool = False, in_list: bool = False) -> None:
        if hidden(node):
            return
        name = tag(node)
        toc = toc or name == "nav" or node.get("role") == "navigation"
        in_list = in_list or name == "li"
        if name == "table":
            # A tiny table containing only an item heading is a layout device.
            # Every other table stays opaque, including nested and financial tables.
            text = normalize(
                " ".join(visible_text(c) for c in node.iter() if tag(c) in {"td", "th"})
            )
            cells = [c for c in node.iter() if tag(c) in {"td", "th"}]
            layout_heading = (
                0 < len(text) <= 220
                and LABEL.match(text) is not None
                and sum(bool(normalize(visible_text(c))) for c in cells) <= 4
                and len(list(node.iter("tr"))) <= 3
                and len(list(node.iter("table"))) == 1
                and len(re.findall(r"\bitem\s+\d", text, re.I)) <= 1
                and not any(
                    re.fullmatch(r"[\s$(),.\d%+-]+", visible_text(c))
                    for c in cells
                    if normalize(visible_text(c))
                )
            )
            links = list(node.iter("a"))
            toc = toc or sum(bool(a.get("href", "").startswith("#")) for a in links) > 2
            append(
                DraftBlock(
                    "heading" if layout_heading else "table",
                    text if layout_heading else "[TABLE]",
                    locator(node),
                    layout_heading,
                    toc,
                )
            )
            return
        pieces: list[str] = []
        native_heading = name in {"h1", "h2", "h3", "h4", "h5", "h6"}
        styled = (
            native_heading
            or node.get("role") == "heading"
            or any(
                tag(c) in {"b", "strong"}
                or re.search(r"font-weight\s*:\s*(?:bold|[6-9]00)", c.get("style", ""))
                for c in node.iter()
                if isinstance(c.tag, str)
            )
        )
        # Do not make a prose sentence into a heading merely because one word is bold.
        link_text = normalize(" ".join(visible_text(a) for a in node.iter("a") if a.get("href")))

        def flush() -> None:
            text = normalize("".join(pieces))
            pieces.clear()
            if not text:
                return
            heading = native_heading or (
                len(text) <= 220 and styled and (bool(LABEL.match(text)) or text.isupper())
            )
            kind: BlockKind = "heading" if heading else ("list" if in_list else "paragraph")
            linked = bool(link_text) and text in link_text
            append(DraftBlock(kind, text, locator(node), heading, toc or linked))

        def inline(child: etree._Element) -> None:
            if hidden(child):
                return
            if tag(child) in BOUNDARIES:
                flush()
                visit(child, toc, in_list)
                return
            if tag(child) == "br":
                pieces.append(" ")
            pieces.append(child.text or "")
            for sub in child:
                inline(sub)
                pieces.append(sub.tail or "")

        pieces.append(node.text or "")
        for child in node:
            inline(child)
            pieces.append(child.tail or "")
        flush()

    visit(root)
    if not blocks:
        raise ParseError("no_visible_content")

    # Unlinked text TOCs: a dense run of labels repeated later in the body.
    # Repetition is required so short genuine adjacent sections are not discarded.
    def label_key(block: DraftBlock) -> str | None:
        if not LABEL.match(block.text) or len(block.text) > 220:
            return None
        return re.sub(r"\s+\d+\s*$", "", block.text).casefold()

    keys = [label_key(b) for b in blocks]
    i = 0
    while i < len(blocks):
        end = i
        while end < len(blocks) and keys[end] is not None and keys[end] not in keys[i:end]:
            end += 1
        repeated_items = [
            key
            for key in keys[i:end]
            if key is not None and key.startswith("item") and key in keys[end:]
        ]
        if len(repeated_items) >= 3:
            for j in range(i, end):
                blocks[j] = replace(blocks[j], toc=True)
        i = max(i + 1, end)
    return tuple(blocks)
