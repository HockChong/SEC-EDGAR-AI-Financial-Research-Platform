"""Canonical v1 records. No parsing, selection, storage I/O or AI authority."""

import hashlib
import json
import re
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, ClassVar, Literal, Self
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    model_validator,
)

from sec_research.contracts.sec import Filing, Source

Text = Annotated[str, Field(min_length=1, pattern=r"\S")]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Cik = Annotated[
    str, Field(pattern=r"^[0-9]{10}$"), AfterValidator(lambda value: _nonzero_cik(value))
]
Accession = Annotated[str, Field(pattern=r"^[0-9]{10}-[0-9]{2}-[0-9]{6}$")]
RecordId = Annotated[str, Field(pattern=r"^[a-z_]+:[0-9a-f]{64}$")]
Ordinal = Annotated[int, Field(strict=True, ge=0)]
PositiveInt = Annotated[int, Field(strict=True, ge=1)]
QualityState = Literal["passed", "warning", "failed"]


def _nonzero_cik(value: str) -> str:
    if int(value) == 0:
        raise ValueError("CIK must be nonzero")
    return value


def _decimal_input(value: object) -> object:
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError("decimal requires a lexical string, integer or Decimal; floats forbidden")
    return value


ExactDecimal = Annotated[Decimal, BeforeValidator(_decimal_input), Field(allow_inf_nan=False)]


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp requires an explicit timezone")
    return value.astimezone(UTC)


UtcTimestamp = Annotated[datetime, AfterValidator(_utc)]


def canonical_bytes(value: object) -> bytes:
    """id-1: sorted JSON keys, UTF-8, compact separators, no NaN or float conversion."""
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def stable_id(namespace: str, payload: object) -> str:
    if not re.fullmatch(r"[a-z_]+", namespace):
        raise ValueError("invalid identity namespace")
    return (
        f"{namespace}:{hashlib.sha256(canonical_bytes(['id-1', namespace, payload])).hexdigest()}"
    )


class ValueModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, hide_input_in_errors=True, revalidate_instances="always"
    )


class Record(ValueModel):
    """Content identity includes all fields except id, including processing versions."""

    namespace: ClassVar[str]
    schema_version: Literal["canonical-1"] = "canonical-1"
    pipeline_version: Text
    id: RecordId | None = None

    @model_validator(mode="after")
    def identity(self) -> Self:
        expected = stable_id(self.namespace, self.model_dump(mode="json", exclude={"id"}))
        if self.id is not None and self.id != expected:
            raise ValueError("record ID does not match canonical content")
        object.__setattr__(self, "id", expected)
        return self


class SourceReference(ValueModel):
    """Artifact identity, deliberately independent of fetch time and local storage paths."""

    source: Source
    sha256: Sha256
    byte_count: Ordinal


class SourceLocator(ValueModel):
    kind: Literal["dom", "json_pointer"]
    path: Text
    # Character offsets are into a named normalized text, never raw HTML bytes.
    text_sha256: Sha256 | None = None
    start: Ordinal | None = None
    end: Ordinal | None = None

    @model_validator(mode="after")
    def location(self) -> Self:
        if not self.path.startswith("/"):
            raise ValueError("locator must be absolute")
        if self.kind == "json_pointer" and re.search(r"~(?![01])", self.path):
            raise ValueError("invalid JSON pointer escape")
        offsets = (self.start, self.end, self.text_sha256)
        if any(value is not None for value in offsets):
            if any(value is None for value in offsets) or self.kind != "dom":
                raise ValueError("text offsets require a DOM locator and named representation")
            if self.start is not None and self.end is not None and self.start >= self.end:
                raise ValueError("offsets must be a nonempty half-open interval")
        return self


class Company(Record):
    namespace = "company"
    cik: Cik
    legal_name: Text
    tickers: tuple[Text, ...] = ()
    sic: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None = None
    fiscal_year_end: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None = None
    source: SourceReference

    @model_validator(mode="after")
    def company_source(self) -> Self:
        if self.source.source.kind not in {"companies", "submissions", "company_facts"}:
            raise ValueError("company requires a company metadata source")
        if self.source.source.cik not in {None, self.cik}:
            raise ValueError("company source CIK mismatch")
        if self.fiscal_year_end is not None:
            date(2000, int(self.fiscal_year_end[:2]), int(self.fiscal_year_end[2:]))
        return self


class CanonicalFiling(Record):
    namespace = "filing"
    filing: Filing
    source: SourceReference
    amends_accession: Accession | None = None

    @model_validator(mode="after")
    def filing_source(self) -> Self:
        source = self.source.source
        if source.kind not in {"submissions", "history", "filing"}:
            raise ValueError("filing requires submissions, history or filing source")
        if source.cik != self.filing.cik:
            raise ValueError("filing source CIK mismatch")
        if source.kind == "filing" and source.filing != self.filing:
            raise ValueError("filing source metadata mismatch")
        if self.filing.accepted_at is not None:
            _utc(self.filing.accepted_at)
        if self.amends_accession is not None and (
            not self.filing.form.endswith("/A") or self.amends_accession == self.filing.accession
        ):
            raise ValueError("amendment relationship requires a distinct original accession")
        return self


class DocumentVersion(Record):
    namespace = "document"
    filing_id: RecordId
    source: SourceReference
    filename: Text
    role: Literal["primary", "exhibit"]
    parser_version: Text
    text_sha256: Sha256 | None = None

    @model_validator(mode="after")
    def document_source(self) -> Self:
        filing = self.source.source.filing
        if self.source.source.kind != "filing" or filing is None:
            raise ValueError("document requires a Bronze filing source")
        if self.filename != filing.primary_document or self.role != "primary":
            raise ValueError("Phase 2 supports primary documents only")
        return self


class Section(Record):
    namespace = "section"
    document_id: RecordId
    parent_section_id: RecordId | None = None
    form: Literal["10-K", "10-Q", "10-K/A", "10-Q/A"]
    part: Literal["I", "II", "III", "IV"] | None = None
    item: Annotated[str, Field(pattern=r"^[0-9]{1,2}[A-C]?$")] | None = None
    classification: Literal["classified", "unclassified", "ambiguous"]
    heading: str
    ordinal: Ordinal
    locator: SourceLocator
    first_block_ordinal: Ordinal
    last_block_ordinal: Ordinal
    quality: QualityState

    @model_validator(mode="after")
    def boundaries(self) -> Self:
        if self.first_block_ordinal > self.last_block_ordinal:
            raise ValueError("section boundaries are reversed")
        if self.locator.kind != "dom":
            raise ValueError("section requires a DOM locator")
        if self.classification == "classified":
            if self.item is None or (self.form.startswith("10-Q") and self.part not in {"I", "II"}):
                raise ValueError("classified section requires form-aware item/part")
        elif self.quality == "passed":
            raise ValueError("uncertain section must retain a quality warning or failure")
        return self


class ContentBlock(Record):
    namespace = "block"
    document_id: RecordId
    section_id: RecordId | None
    kind: Literal["heading", "paragraph", "list", "table", "footnote", "other"]
    ordinal: Ordinal
    text: str
    text_sha256: Sha256
    locator: SourceLocator

    @model_validator(mode="after")
    def content_hash(self) -> Self:
        if hashlib.sha256(self.text.encode("utf-8")).hexdigest() != self.text_sha256:
            raise ValueError("content text checksum mismatch")
        if self.locator.kind != "dom":
            raise ValueError("content block requires a DOM locator")
        return self


class StructuredTable(Record):
    namespace = "table"
    document_id: RecordId
    section_id: RecordId | None
    block_id: RecordId
    locator: SourceLocator
    rows: PositiveInt
    columns: PositiveInt
    title: str
    unit_hints: tuple[Text, ...] = ()
    scale_hint: ExactDecimal | None = None
    footnotes: tuple[Text, ...] = ()
    retrieval_text: str
    quality: QualityState

    @model_validator(mode="after")
    def table_shape(self) -> Self:
        if self.locator.kind != "dom":
            raise ValueError("table requires a DOM locator")
        if self.scale_hint is not None and self.scale_hint <= 0:
            raise ValueError("table scale must be positive or unknown")
        return self


class TableCell(Record):
    namespace = "cell"
    table_id: RecordId
    row: Ordinal
    column: Ordinal
    row_span: PositiveInt = 1
    column_span: PositiveInt = 1
    is_header: bool
    header_ids: tuple[RecordId, ...] = ()
    raw_text: str
    display_text: str
    unit_hint: Text | None = None
    footnote_markers: tuple[Text, ...] = ()
    numeric_status: Literal["parsed", "not_numeric", "empty", "uncertain"]
    value: ExactDecimal | None = None
    locator: SourceLocator

    @model_validator(mode="after")
    def parsed_value(self) -> Self:
        if (self.numeric_status == "parsed") != (self.value is not None):
            raise ValueError("only parsed cells carry a numeric value")
        if self.numeric_status == "empty" and (self.raw_text.strip() or self.display_text.strip()):
            raise ValueError("empty cell must not discard text")
        if self.locator.kind != "dom":
            raise ValueError("table cell requires a DOM locator")
        return self


class ReportingPeriod(ValueModel):
    kind: Literal["instant", "duration"]
    start: date | None = None
    end: date
    duration_class: Literal["quarter", "year_to_date", "annual", "other", "unknown"] | None = None
    classification_policy: Text | None = None

    @model_validator(mode="after")
    def measurement(self) -> Self:
        if self.kind == "instant":
            if any(
                x is not None for x in (self.start, self.duration_class, self.classification_policy)
            ):
                raise ValueError("instant cannot contain duration metadata")
        else:
            if self.start is None or self.start > self.end or self.duration_class is None:
                raise ValueError("duration requires ordered dates and explicit classification")
            if self.duration_class != "unknown" and self.classification_policy is None:
                raise ValueError("duration classification requires a versioned policy")
        return self


class Dimension(ValueModel):
    axis: Text
    member: Text


class FinancialFact(Record):
    namespace = "fact"
    cik: Cik
    taxonomy: Text
    concept: Text
    raw_value: Annotated[
        str, Field(pattern=r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?$")
    ]
    value: ExactDecimal
    unit: Text
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")] | None = None
    period: ReportingPeriod
    accession: Accession
    form: Text
    filed: date
    accepted_at: UtcTimestamp | None = None
    fy: Annotated[int, Field(strict=True, ge=1900, le=9999)] | None = None
    fp: Text | None = None
    frame: Text | None = None
    context_id: Text | None = None
    context_status: Literal["unknown", "verified"]
    dimensions: tuple[Dimension, ...] | None = None
    source: SourceReference
    locator: SourceLocator
    normalizer_version: Text
    quality: QualityState

    @model_validator(mode="after")
    def observation(self) -> Self:
        if Decimal(self.raw_value) != self.value:
            raise ValueError("canonical value must equal the source decimal without scaling")
        if self.source.source.kind != "company_facts" or self.source.source.cik != self.cik:
            raise ValueError("fact requires a matching Company Facts source")
        if self.locator.kind != "json_pointer":
            raise ValueError("Company Facts requires a JSON pointer")
        if self.period.end > self.filed:
            raise ValueError("measurement end cannot follow filing availability")
        if self.currency is not None and self.unit.split("/")[0] != self.currency:
            raise ValueError("currency conflicts with unit")
        if self.context_status == "unknown":
            if self.dimensions is not None or self.context_id is not None:
                raise ValueError("unknown context must not imply verified dimensions")
        elif self.dimensions is None:
            raise ValueError("verified context requires explicit dimensions")
        if self.dimensions is not None:
            axes = [dimension.axis for dimension in self.dimensions]
            if axes != sorted(set(axes)):
                raise ValueError("dimensions must have unique axes in sorted order")
        return self

    @property
    def observation_id(self) -> str:
        """Logical reporting identity; source occurrences remain distinct canonical rows."""
        fields = {
            "cik",
            "taxonomy",
            "concept",
            "value",
            "unit",
            "currency",
            "period",
            "accession",
            "form",
            "filed",
            "accepted_at",
            "context_id",
            "context_status",
            "dimensions",
        }
        payload = self.model_dump(mode="json", include=fields)
        # Decimal.normalize() can round under the ambient context; strip lexical zeros instead.
        value = format(self.value, "f")
        payload["value"] = (value.rstrip("0").rstrip(".") if "." in value else value) or "0"
        if self.value == 0:
            payload["value"] = "0"
        # Classification is processing metadata; actual measurement dates define the observation.
        payload["period"] = self.period.model_dump(mode="json", include={"kind", "start", "end"})
        return stable_id("observation", payload)


class SourceProvenance(Record):
    namespace = "provenance"
    entity_id: RecordId
    source: SourceReference
    locator: SourceLocator | None = None
    fetch_id: UUID
    fetched_at: UtcTimestamp
    input_entity_ids: tuple[RecordId, ...] = ()


class ResearchChunk(Record):
    namespace = "chunk"
    document_id: RecordId
    section_id: RecordId
    source_block_ids: Annotated[tuple[RecordId, ...], Field(min_length=1)]
    related_table_ids: tuple[RecordId, ...] = ()
    ordinal: Ordinal
    kind: Literal["narrative", "table"]
    text: Text
    text_sha256: Sha256
    token_count: PositiveInt
    tokenizer_version: Text
    chunker_version: Text
    source: SourceReference

    @model_validator(mode="after")
    def chunk_source(self) -> Self:
        if self.source.source.kind != "filing":
            raise ValueError("chunk requires original filing provenance")
        if hashlib.sha256(self.text.encode("utf-8")).hexdigest() != self.text_sha256:
            raise ValueError("chunk text checksum mismatch")
        if len(set(self.source_block_ids)) != len(self.source_block_ids):
            raise ValueError("chunk source blocks must be unique and ordered")
        if self.kind == "table" and not self.related_table_ids:
            raise ValueError("table chunk must identify its structured table")
        return self


class ConceptMapping(ValueModel):
    taxonomy: Text
    concept: Text
    priority: Ordinal


class MetricDefinition(Record):
    namespace = "metric"
    metric_name: Text
    metric_version: Text
    description: Text
    mapping_status: Literal["supported", "unsupported", "ambiguous"]
    concepts: tuple[ConceptMapping, ...] = ()
    period_kind: Literal["instant", "duration"]
    unit: Text
    context_requirement: Literal[
        "verified_consolidated", "verified_dimensions", "company_facts_entity"
    ]
    selection_policy_version: Text
    formula_id: Text | None = None
    formula_version: Text | None = None
    input_metric_ids: tuple[RecordId, ...] = ()
    sign_policy: Text
    denominator_policy: Text
    rounding_policy: Text
    limitations: tuple[Text, ...] = ()

    @model_validator(mode="after")
    def definition(self) -> Self:
        if (self.formula_id is None) != (self.formula_version is None):
            raise ValueError("formula identity and version must be supplied together")
        if self.mapping_status == "supported" and not self.concepts and self.formula_id is None:
            raise ValueError("supported metric requires concepts or a registered formula")
        if self.formula_id is not None and not self.input_metric_ids:
            raise ValueError("derived metric requires explicit inputs")
        if self.mapping_status != "supported" and not self.limitations:
            raise ValueError("unsupported or ambiguous mapping requires an explanation")
        return self


class QualityEvent(Record):
    namespace = "quality"
    entity_id: RecordId
    rule: Text
    rule_version: Text
    state: QualityState
    reason_code: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]
    disposition: Literal["accept", "retain_with_warning", "quarantine", "block_publication"]
    source: SourceReference

    @model_validator(mode="after")
    def disposition_matches(self) -> Self:
        allowed = {
            "passed": {"accept"},
            "warning": {"retain_with_warning"},
            "failed": {"quarantine", "block_publication"},
        }
        if self.disposition not in allowed[self.state]:
            raise ValueError("quality state and disposition conflict")
        return self


class DatasetObject(ValueModel):
    dataset: Text
    path: Text
    sha256: Sha256
    row_count: Ordinal
    schema_sha256: Sha256

    @model_validator(mode="after")
    def relative_path(self) -> Self:
        if (
            self.path.startswith("/")
            or "\\" in self.path
            or ":" in self.path
            or any(part in {"", ".", ".."} for part in self.path.split("/"))
            or not self.path.endswith(".parquet")
        ):
            raise ValueError("dataset path must be a safe relative Parquet path")
        return self


class DatasetPublication(Record):
    namespace = "publication"
    dataset_version: Text
    layer: Literal["silver", "gold"]
    code_revision: Text
    config_sha256: Sha256
    parser_version: Text | None = None
    normalizer_version: Text | None = None
    chunker_version: Text | None = None
    selection_policy_version: Text | None = None
    input_publication_ids: tuple[RecordId, ...] = ()
    input_source_sha256s: Annotated[tuple[Sha256, ...], Field(min_length=1)]
    objects: Annotated[tuple[DatasetObject, ...], Field(min_length=1)]
    state: Literal["staged", "validated", "published", "failed"]
    quality: QualityState
    quality_event_ids: tuple[RecordId, ...] = ()
    validated_at: UtcTimestamp | None = None
    published_at: UtcTimestamp | None = None

    @model_validator(mode="after")
    def publication(self) -> Self:
        paths = [item.path for item in self.objects]
        if paths != sorted(set(paths)):
            raise ValueError("dataset objects must have unique paths in sorted order")
        hashes = self.input_source_sha256s
        if list(hashes) != sorted(set(hashes)):
            raise ValueError("input hashes must be unique and sorted")
        if self.state in {"validated", "published"} and (
            self.validated_at is None or self.quality == "failed"
        ):
            raise ValueError("publication requires successful validation")
        if self.state == "published":
            if self.published_at is None or (
                self.validated_at is not None and self.published_at < self.validated_at
            ):
                raise ValueError("publication must follow validation")
        elif self.published_at is not None:
            raise ValueError("only published manifests carry a publication timestamp")
        return self


CANONICAL_MODELS: tuple[type[Record], ...] = (
    Company,
    CanonicalFiling,
    DocumentVersion,
    Section,
    ContentBlock,
    StructuredTable,
    TableCell,
    FinancialFact,
    SourceProvenance,
    ResearchChunk,
    MetricDefinition,
    QualityEvent,
    DatasetPublication,
)
