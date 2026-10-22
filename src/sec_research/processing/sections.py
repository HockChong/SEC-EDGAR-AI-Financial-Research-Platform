"""Form-aware structural classification; regex recognizes labels, never splits HTML."""

import re
from dataclasses import dataclass
from typing import Literal

from sec_research.processing.blocks import DraftBlock

CLASSIFIER_VERSION = "sec-sections-1"
Part = Literal["I", "II", "III", "IV"]
PARTS: dict[str, Part] = {"I": "I", "II": "II", "III": "III", "IV": "IV"}
PART = re.compile(r"^part\s+(IV|III|II|I)\b[\s.\-\u2013\u2014:]*(.*)$", re.I)
ITEM = re.compile(r"^item\s+(\d{1,2}[A-C]?)\b[\s.\-\u2013\u2014:]*(.*)$", re.I)
K_ITEMS = (
    "1",
    "1A",
    "1B",
    "1C",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "7A",
    "8",
    "9",
    "9A",
    "9B",
    "9C",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
)
Q_ITEMS = {"I": ("1", "2", "3", "4"), "II": ("1", "1A", "2", "3", "4", "5", "6")}


@dataclass(frozen=True)
class Boundary:
    first: int
    part: Part | None
    item: str | None
    classification: Literal["classified", "unclassified", "ambiguous"]
    reason: str | None


def annual_part(item: str) -> Part:
    number = int(item.rstrip("ABC"))
    return "I" if number <= 4 else "II" if number <= 9 else "III" if number <= 14 else "IV"


def classify(blocks: tuple[DraftBlock, ...], form: str) -> tuple[Boundary, ...]:
    annual = form.startswith("10-K")
    boundaries = [Boundary(0, None, None, "unclassified", "unclassified_content")]
    part: Part | None = None
    last_rank = -1
    seen: set[tuple[Part | None, str]] = set()
    for i, block in enumerate(blocks):
        if block.toc or block.kind == "table" or len(block.text) > 220:
            continue
        text = block.text
        if text.upper().strip(" .:") in {"SIGNATURE", "SIGNATURES"}:
            boundaries.append(Boundary(i, None, None, "unclassified", "non_item_section"))
            continue
        pm = PART.match(text)
        if pm:
            proposed = PARTS[pm[1].upper()]
            # Repeated page headers must not reset item order or the active section.
            if proposed != part and (
                part is None or list(PARTS).index(proposed) > list(PARTS).index(part)
            ):
                part = proposed
                last_rank = -1
                boundaries.append(Boundary(i, part, None, "unclassified", "part_preamble"))
            text = pm[2]
        match = ITEM.match(text)
        if not match:
            continue
        item, title = match[1].upper(), match[2].strip()
        # Bare running headers ("Item 1") are retained, never accepted as boundaries.
        if not title:
            continue
        # Recognize a short standalone heading only with DOM emphasis or a conventional
        # title. Prose references such as "Item 7 discusses ..." are not boundaries.
        conventional = re.match(
            r"(?:business|risk factors|unresolved staff|cybersecurity|properties|legal proceedings|"
            r"mine safety|market for|\[?reserved|management[\u2019']?s|"
            r"financial statements|quantitative|"
            r"changes in|controls and|other information|disclosure regarding|directors|executive|"
            r"security ownership|certain relationships|principal accountant|exhibits?|form 10-k|"
            r"unregistered sales|defaults upon)",
            title,
            re.I,
        )
        if not block.heading and not conventional:
            continue
        inferred = annual_part(item) if annual and item in K_ITEMS else part
        allowed = K_ITEMS if annual else Q_ITEMS.get(inferred or "", ())
        if not annual and inferred not in {"I", "II"}:
            boundary = Boundary(i, None, item, "ambiguous", "missing_part")
        elif item not in allowed:
            boundary = Boundary(i, inferred, item, "ambiguous", "invalid_form_item")
        elif title.startswith("?"):
            boundary = Boundary(i, inferred, item, "ambiguous", "uncertain_heading")
        elif (inferred, item) in seen:
            # Preserve repeated headings as content without introducing duplicate sections.
            continue
        else:
            rank = allowed.index(item)
            if rank < last_rank:
                boundary = Boundary(i, inferred, item, "ambiguous", "item_order_conflict")
            else:
                boundary = Boundary(i, inferred, item, "classified", None)
                last_rank = rank
                seen.add((inferred, item))
        if boundaries[-1].first == i:
            boundaries[-1] = boundary
        else:
            boundaries.append(boundary)
    # Part at block zero can create an empty initial segment; keep one boundary per ordinal.
    return tuple({b.first: b for b in boundaries}.values())
