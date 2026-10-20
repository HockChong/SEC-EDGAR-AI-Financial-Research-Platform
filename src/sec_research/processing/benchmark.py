"""Explicit source-inspected boundary labels, independent of classifier predictions."""

from typing import Literal

from sec_research.contracts.canonical import Accession, Cik, Sha256, Text, ValueModel
from sec_research.contracts.parsing import ParsedDocument
from sec_research.processing.blocks import normalize, visible_text
from sec_research.processing.dom import DOM, locator, resolve
from sec_research.processing.sections import Part


class CorpusCase(ValueModel):
    cik: Cik
    form: Literal["10-K", "10-Q"]
    accession: Accession
    source_sha256: Sha256
    split: Literal["development", "held_out"]


class CorpusSplit(ValueModel):
    schema_version: Literal["wp32-split-1"]
    frozen_before_heuristic_development: Literal[True]
    policy: Text
    filings: tuple[CorpusCase, ...]


class BoundaryLabel(ValueModel):
    part: Part
    item: Text
    start_xpath: Text
    end_before_xpath: Text
    heading: Text
    next_heading: Text


class LabeledCase(ValueModel):
    accession: Accession
    source_sha256: Sha256
    split: Literal["development", "held_out"]
    sections: tuple[BoundaryLabel, ...]


class Benchmark(ValueModel):
    schema_version: Literal["wp32-boundaries-1"]
    annotation_method: Text
    human_adjudicated: Literal[False]
    cases: tuple[LabeledCase, ...]


def score_boundaries(
    result: ParsedDocument, dom: DOM, case: LabeledCase
) -> list[dict[str, object]]:
    if result.document.source.sha256 != case.source_sha256:
        raise ValueError("benchmark source checksum mismatch")
    scores: list[dict[str, object]] = []
    for label in case.sections:
        start_node = resolve(dom.root, label.start_xpath)
        end_node = resolve(dom.root, label.end_before_xpath)
        if normalize(visible_text(start_node)) != label.heading or (
            normalize(visible_text(end_node)) != label.next_heading
        ):
            raise ValueError("benchmark source heading differs from annotation")
        start, end = locator(start_node), locator(end_node)
        start_blocks = [b.ordinal for b in result.blocks if b.locator.path == start]
        end_blocks = [b.ordinal for b in result.blocks if b.locator.path == end]
        predicted = [
            s
            for s in result.sections
            if s.classification == "classified" and s.part == label.part and s.item == label.item
        ]
        start_ok = (
            len(predicted) == 1
            and bool(start_blocks)
            and (predicted[0].first_block_ordinal == start_blocks[0])
        )
        end_ok = (
            len(predicted) == 1
            and bool(end_blocks)
            and (predicted[0].last_block_ordinal == end_blocks[0] - 1)
        )
        scores.append(
            {
                "part": label.part,
                "item": label.item,
                "start_correct": start_ok,
                "end_correct": end_ok,
                "both_correct": start_ok and end_ok,
            }
        )
    return scores
