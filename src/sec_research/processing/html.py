"""Pure deterministic Bronze HTML -> canonical sections and narrative/table blocks."""

import hashlib
from collections.abc import Iterable, Iterator

from pydantic import ValidationError

from sec_research.contracts.bronze import validated_source
from sec_research.contracts.canonical import (
    CanonicalFiling,
    ContentBlock,
    DocumentVersion,
    QualityEvent,
    Record,
    Section,
    SourceLocator,
    SourceProvenance,
)
from sec_research.contracts.parsing import ParsedDocument, ParseFailure
from sec_research.ingestion.ports import Fetch
from sec_research.processing.blocks import extract_blocks
from sec_research.processing.dom import PARSER_VERSION, PIPELINE_VERSION, ParseError, load_dom
from sec_research.processing.sections import CLASSIFIER_VERSION, classify


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record_id(record: Record) -> str:
    assert record.id is not None
    return record.id


def parse_batch(inputs: Iterable[tuple[Fetch, bytes]]) -> Iterator[ParsedDocument | ParseFailure]:
    """A rejected document cannot discard the successfully parsed neighboring inputs."""
    for fetch, body in inputs:
        try:
            yield parse_html(fetch, body)
        except ParseError as error:
            yield ParseFailure(fetch_id=fetch.id, source_sha256=fetch.sha256, code=error.code)


def parse_html(fetch: Fetch, body: bytes) -> ParsedDocument:
    """No I/O. Caller verifies immutable manifest through the Bronze adapter/reconciliation."""
    try:
        source = validated_source(fetch, body)
    except (ValueError, ValidationError):
        raise ParseError("source_integrity") from None
    metadata = source.source.filing
    if source.source.kind != "filing" or metadata is None:
        raise ParseError("not_a_filing")
    dom = load_dom(body)
    drafts = extract_blocks(dom.root)
    text_hash = digest("\n".join(b.text for b in drafts))
    filing = CanonicalFiling(pipeline_version=PIPELINE_VERSION, filing=metadata, source=source)
    document = DocumentVersion(
        pipeline_version=PIPELINE_VERSION,
        filing_id=record_id(filing),
        source=source,
        filename=metadata.primary_document,
        role="primary",
        parser_version=PARSER_VERSION + "/" + CLASSIFIER_VERSION,
        text_sha256=text_hash,
    )
    offsets = 0
    locators: list[SourceLocator] = []
    for draft in drafts:
        locators.append(
            SourceLocator(
                kind="dom",
                path=draft.path,
                text_sha256=text_hash,
                start=offsets,
                end=offsets + len(draft.text),
            )
        )
        offsets += len(draft.text) + 1
    boundaries = classify(drafts, metadata.form)
    sections: list[Section] = []
    events: list[QualityEvent] = []

    def warning(entity_id: str, reason: str) -> None:
        events.append(
            QualityEvent(
                pipeline_version=PIPELINE_VERSION,
                entity_id=entity_id,
                rule="html_sections",
                rule_version=document.parser_version,
                state="warning",
                reason_code=reason,
                disposition="retain_with_warning",
                source=source,
            )
        )

    for reason in dom.warnings:
        warning(record_id(document), reason)
    if any(b.toc for b in drafts):
        warning(record_id(document), "toc_content_retained")
    for i, boundary in enumerate(boundaries):
        end = boundaries[i + 1].first - 1 if i + 1 < len(boundaries) else len(drafts) - 1
        section = Section(
            pipeline_version=PIPELINE_VERSION,
            document_id=record_id(document),
            form=metadata.form,
            part=boundary.part,
            item=boundary.item,
            classification=boundary.classification,
            heading=drafts[boundary.first].text,
            ordinal=i,
            locator=locators[boundary.first],
            first_block_ordinal=boundary.first,
            last_block_ordinal=end,
            quality="passed" if boundary.reason is None else "warning",
        )
        sections.append(section)
        if boundary.reason:
            warning(record_id(section), boundary.reason)
    priority = (
        (("I", "1"), ("I", "1A"), ("II", "7"), ("II", "8"))
        if metadata.form.startswith("10-K")
        else (("I", "1"), ("I", "2"), ("II", "1A"))
    )
    classified = {(s.part, s.item) for s in sections if s.classification == "classified"}
    for part, item in priority:
        if (part, item) not in classified:
            warning(record_id(document), f"missing_priority_{part.lower()}_{item.lower()}")
    blocks: list[ContentBlock] = []
    for section in sections:
        for ordinal in range(section.first_block_ordinal, section.last_block_ordinal + 1):
            draft = drafts[ordinal]
            blocks.append(
                ContentBlock(
                    pipeline_version=PIPELINE_VERSION,
                    document_id=record_id(document),
                    section_id=record_id(section),
                    kind=draft.kind,
                    ordinal=ordinal,
                    text=draft.text,
                    text_sha256=digest(draft.text),
                    locator=locators[ordinal],
                )
            )
    return ParsedDocument(
        classifier_version=CLASSIFIER_VERSION,
        encoding=dom.encoding,
        filing=filing,
        document=document,
        sections=tuple(sections),
        blocks=tuple(blocks),
        quality_events=tuple(events),
        provenance=SourceProvenance(
            pipeline_version=PIPELINE_VERSION,
            entity_id=record_id(document),
            source=source,
            locator=SourceLocator(kind="dom", path="/*[1]"),
            fetch_id=fetch.id,
            fetched_at=fetch.fetched_at,
            input_entity_ids=(record_id(filing),),
        ),
    )
