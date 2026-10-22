"""WP3.5 publication and serving contracts; no chunking or financial inference."""

import hashlib
from typing import Literal, Self

from pydantic import model_validator

from sec_research.contracts.canonical import (
    DatasetPublication,
    QualityState,
    Record,
    RecordId,
    Sha256,
    SourceLocator,
    SourceReference,
    Text,
    UtcTimestamp,
    ValueModel,
    canonical_bytes,
    stable_id,
)
from sec_research.contracts.tables import ExtractedTable, TableText
from sec_research.contracts.xbrl import (
    ConceptMetadata,
    FactOccurrence,
    FactSelection,
    SelectionRequest,
)
from sec_research.ingestion.ports import Fetch

PIPELINE = "datasets-1"
LIMITATIONS = (
    "wp32_jpmorgan_quarterly_sections_unknown",
    "wp33_rev_001_through_006_unresolved",
    "wp33_independent_financial_adjudication_deferred",
    "wp34_independent_financial_accuracy_unverified",
    "company_facts_dimensions_unknown",
    "reported_metrics_have_narrow_concept_coverage",
)


class ProcessingVersions(ValueModel):
    canonical: Literal["canonical-1"] = "canonical-1"
    transform: Literal["datasets-1"] = "datasets-1"
    parser: Text
    classifier: Text
    tables: Literal["sec-tables-2"] = "sec-tables-2"
    table_text: Literal["table-text-2"] = "table-text-2"
    table_numbers: Literal["table-numeric-1"] = "table-numeric-1"
    normalizer: Literal["company-facts-1"] = "company-facts-1"
    selection: Literal["fact-selection-1"] = "fact-selection-1"
    metrics: Literal["reported-metrics-1"] = "reported-metrics-1"
    arrow: Text
    encoding: Literal["arrow-1"] = "arrow-1"


class BuildSpec(ValueModel):
    code_revision: Text
    code_sha256: Sha256
    lock_sha256: Sha256
    versions: ProcessingVersions
    # Pinned logical run clock; actual activation time is a PostgreSQL audit event.
    run_at: UtcTimestamp
    requests: tuple[SelectionRequest, ...] = ()


class SourceEntry(Record):
    namespace = "dataset_source"
    fetch: Fetch
    source: SourceReference
    disposition: Literal["transformed", "reference_only"]

    @model_validator(mode="after")
    def identity_matches(self) -> Self:
        if (self.fetch.source, self.fetch.sha256, self.fetch.byte_count) != (
            self.source.source,
            self.source.sha256,
            self.source.byte_count,
        ):
            raise ValueError("source entry differs from fetch")
        transformed = self.fetch.source.kind in {"filing", "company_facts"}
        if transformed != (self.disposition == "transformed"):
            raise ValueError("unsupported source transformation")
        return self


class ParseMetadata(Record):
    namespace = "parse_metadata"
    document_id: RecordId
    classifier_version: Text
    encoding: Text
    source: SourceReference


class TableDetail(Record):
    namespace = "table_detail"
    document_id: RecordId
    source: SourceReference
    extraction: ExtractedTable


class TableRepresentation(Record):
    namespace = "table_representation"
    document_id: RecordId
    source: SourceReference
    representation: TableText


class SourceOccurrence(Record):
    namespace = "source_occurrence"
    company_id: RecordId
    source: SourceReference
    occurrence: FactOccurrence


class SourceConcept(Record):
    namespace = "source_concept"
    company_id: RecordId
    source: SourceReference
    metadata: ConceptMetadata


class ResearchEvidence(Record):
    """One source block, ready for WP3.6; never described as a tokenized chunk."""

    namespace = "research_evidence"
    document_id: RecordId
    section_id: RecordId
    block_id: RecordId
    ordinal: int
    kind: Literal["heading", "paragraph", "list", "table", "footnote", "other"]
    text: str
    text_sha256: Sha256
    section_classification: Literal["classified", "unclassified", "ambiguous"]
    quality: QualityState
    source: SourceReference
    locator: SourceLocator


class SelectionEvidence(Record):
    namespace = "selection_evidence"
    result: FactSelection


class Citation(Record):
    namespace = "citation"
    target_id: RecordId
    target_dataset: Text
    source_entity_id: RecordId
    source: SourceReference
    locator: SourceLocator
    quality: QualityState


class Snapshot(Record):
    namespace = "snapshot"
    spec: BuildSpec
    source_entries: tuple[SourceEntry, ...]
    silver: DatasetPublication
    gold: DatasetPublication
    limitations: tuple[Text, ...] = LIMITATIONS

    @model_validator(mode="after")
    def complete_pair(self) -> Self:
        if not self.source_entries or len({e.fetch.id for e in self.source_entries}) != len(
            self.source_entries
        ):
            raise ValueError("empty or duplicate input fetches")
        if self.silver.layer != "silver" or self.gold.layer != "gold":
            raise ValueError("invalid publication layers")
        if self.gold.input_publication_ids != (self.silver.id,):
            raise ValueError("Gold must pin its Silver publication")
        hashes = tuple(sorted({e.source.sha256 for e in self.source_entries}))
        config_hash = hashlib.sha256(canonical_bytes(self.spec.model_dump(mode="json"))).hexdigest()
        version = stable_id(
            "dataset",
            {
                "spec": self.spec.model_dump(mode="json"),
                "inputs": sorted(e.id for e in self.source_entries if e.id is not None),
            },
        )
        for publication in (self.silver, self.gold):
            if publication.state != "validated" or publication.input_source_sha256s != hashes:
                raise ValueError("snapshot must contain complete validated publications")
            if publication.dataset_version != self.silver.dataset_version:
                raise ValueError("publication version mismatch")
            if publication.code_revision != self.spec.code_revision:
                raise ValueError("publication code mismatch")
            if (
                publication.config_sha256 != config_hash
                or publication.dataset_version != version
                or publication.parser_version != self.spec.versions.parser
                or publication.normalizer_version != self.spec.versions.normalizer
                or publication.selection_policy_version != self.spec.versions.selection
                or publication.pipeline_version != PIPELINE
                or publication.validated_at != self.spec.run_at
            ):
                raise ValueError("inconsistent publication configuration")
        if self.limitations != LIMITATIONS:
            raise ValueError("known limitations must remain visible")
        return self


class DatasetError(Exception):
    """Safe error code; failed work is retryable from immutable inputs."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)
