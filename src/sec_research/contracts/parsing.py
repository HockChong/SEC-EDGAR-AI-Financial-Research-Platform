"""WP3.2 envelope: reuse canonical-1 rows and validate their complete source graph."""

import hashlib
from typing import Literal, Self
from uuid import UUID

from pydantic import model_validator

from sec_research.contracts.canonical import (
    CanonicalFiling,
    ContentBlock,
    DocumentVersion,
    QualityEvent,
    Section,
    Sha256,
    SourceProvenance,
    Text,
    ValueModel,
    canonical_bytes,
)


class ParsedDocument(ValueModel):
    schema_version: Literal["html-result-1"] = "html-result-1"
    classifier_version: Text
    encoding: Text
    filing: CanonicalFiling
    document: DocumentVersion
    sections: tuple[Section, ...]
    blocks: tuple[ContentBlock, ...]
    quality_events: tuple[QualityEvent, ...]
    provenance: SourceProvenance

    @model_validator(mode="after")
    def graph(self) -> Self:
        doc = self.document
        if doc.filing_id != self.filing.id or doc.source != self.filing.source:
            raise ValueError("document/filing source mismatch")
        if not self.blocks or not self.sections:
            raise ValueError("parsed document requires content and complete sections")
        if [b.ordinal for b in self.blocks] != list(range(len(self.blocks))):
            raise ValueError("block ordinals must be contiguous reading order")
        if [s.ordinal for s in self.sections] != list(range(len(self.sections))):
            raise ValueError("section ordinals must be contiguous")
        cursor = 0
        for section in self.sections:
            if (
                section.document_id != doc.id
                or section.form != self.filing.filing.form
                or section.first_block_ordinal != cursor
                or section.last_block_ordinal >= len(self.blocks)
                or section.parent_section_id is not None
            ):
                raise ValueError("sections must partition the document in reading order")
            members = self.blocks[cursor : section.last_block_ordinal + 1]
            if section.locator != members[0].locator:
                raise ValueError("section locator must identify its first block")
            if any(b.document_id != doc.id or b.section_id != section.id for b in members):
                raise ValueError("block/section ownership mismatch")
            cursor = section.last_block_ordinal + 1
        if cursor != len(self.blocks):
            raise ValueError("uncovered content blocks")
        text_hash = hashlib.sha256("\n".join(b.text for b in self.blocks).encode()).hexdigest()
        if doc.text_sha256 != text_hash:
            raise ValueError("normalized document checksum mismatch")
        entities = {doc.id, *(s.id for s in self.sections), *(b.id for b in self.blocks)}
        for event in self.quality_events:
            if event.entity_id not in entities or event.source != doc.source:
                raise ValueError("quality event source mismatch")
        if (
            self.provenance.entity_id != doc.id
            or self.provenance.source != doc.source
            or self.provenance.input_entity_ids != (self.filing.id,)
        ):
            raise ValueError("document provenance mismatch")
        if any(
            row.pipeline_version != doc.pipeline_version
            for row in (
                *self.sections,
                *self.blocks,
                *self.quality_events,
                self.filing,
                self.provenance,
            )
        ):
            raise ValueError("pipeline version mismatch")
        return self

    def logical_bytes(self) -> bytes:
        """Fetch occurrences vary; logical parsing output does not include fetch metadata."""
        return canonical_bytes(self.model_dump(mode="json", exclude={"provenance"}))


class ParseFailure(ValueModel):
    fetch_id: UUID
    source_sha256: Sha256
    code: Text
    disposition: Literal["quarantine"] = "quarantine"
