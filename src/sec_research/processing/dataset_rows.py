"""Pure Silver/Gold transforms over the existing validated processor envelopes."""

from collections import Counter
from collections.abc import Sequence

from sec_research.contracts.canonical import (
    CanonicalFiling,
    Company,
    ContentBlock,
    DocumentVersion,
    FinancialFact,
    QualityEvent,
    Record,
    Section,
    SourceProvenance,
    SourceReference,
    StructuredTable,
)
from sec_research.contracts.datasets import (
    PIPELINE,
    Citation,
    DatasetError,
    ParseMetadata,
    ProcessingVersions,
    ResearchEvidence,
    SourceConcept,
    SourceEntry,
    SourceOccurrence,
    TableDetail,
    TableRepresentation,
)
from sec_research.contracts.parsing import ParsedDocument
from sec_research.contracts.tables import TableExtraction
from sec_research.contracts.xbrl import NormalizedFacts
from sec_research.domain.metrics import METRICS

Rows = dict[str, list[Record]]
HTML_DATASETS = (
    "silver_filings",
    "silver_documents",
    "silver_sections",
    "silver_content_blocks",
    "silver_tables",
    "silver_table_cells",
    "silver_table_details",
    "silver_table_text",
    "silver_parse_metadata",
    "silver_provenance",
    "silver_parse_quality",
)
XBRL_DATASETS = (
    "silver_companies",
    "silver_xbrl_facts",
    "silver_xbrl_occurrences",
    "silver_xbrl_concepts",
    "silver_provenance",
    "silver_parse_quality",
)
GOLD_HTML = ("gold_research_evidence", "gold_tables", "gold_table_text", "gold_citations")
GOLD_XBRL = ("gold_reported_facts", "gold_citations")


def typed[T: Record](rows: Rows, name: str, model: type[T]) -> list[T]:
    values = rows[name]
    if any(not isinstance(r, model) for r in values):
        raise DatasetError("dataset_record_type_mismatch")
    return [r for r in values if isinstance(r, model)]


def same(left: Sequence[Record], right: Sequence[Record]) -> bool:
    return sorted(left, key=lambda r: r.id or "") == sorted(right, key=lambda r: r.id or "")


def html_rows(parsed: ParsedDocument, tables: TableExtraction) -> Rows:
    parsed = ParsedDocument.model_validate(parsed.model_dump())
    tables = TableExtraction.model_validate(tables.model_dump())
    if (tables.document, tables.blocks, tables.sections) != (
        parsed.document,
        parsed.blocks,
        parsed.sections,
    ):
        raise DatasetError("incompatible_table_parse")
    doc = parsed.document
    assert doc.id is not None
    rows: Rows = {
        "silver_filings": [parsed.filing],
        "silver_documents": [doc],
        "silver_sections": list(parsed.sections),
        "silver_content_blocks": list(parsed.blocks),
        "silver_provenance": [parsed.provenance],
        "silver_parse_quality": list(parsed.quality_events),
        "silver_parse_metadata": [
            ParseMetadata(
                pipeline_version=PIPELINE,
                document_id=doc.id,
                source=doc.source,
                classifier_version=parsed.classifier_version,
                encoding=parsed.encoding,
            )
        ],
        "silver_tables": [t.table for t in tables.tables if t.table is not None],
        "silver_table_cells": [c for t in tables.tables for c in t.cells],
        "silver_table_details": [
            TableDetail(
                pipeline_version=PIPELINE,
                document_id=doc.id,
                source=doc.source,
                extraction=t,
            )
            for t in tables.tables
        ],
        "silver_table_text": [
            TableRepresentation(
                pipeline_version=PIPELINE,
                document_id=doc.id,
                source=doc.source,
                representation=t,
            )
            for t in tables.retrieval
        ],
    }
    rows["silver_parse_quality"].append(
        QualityEvent(
            pipeline_version=PIPELINE,
            entity_id=doc.id,
            source=doc.source,
            rule="independent_financial_accuracy",
            rule_version=PIPELINE,
            state="warning",
            reason_code="wp33_financial_accuracy_unverified",
            disposition="retain_with_warning",
        )
    )
    for detail in typed(rows, "silver_table_details", TableDetail):
        item = detail.extraction
        if item.warnings or item.grid_status == "quarantined":
            assert detail.id is not None
            rows["silver_parse_quality"].append(
                QualityEvent(
                    pipeline_version=PIPELINE,
                    entity_id=detail.id,
                    source=doc.source,
                    rule="table_quality",
                    rule_version=PIPELINE,
                    state="failed" if item.grid_status == "quarantined" else "warning",
                    reason_code="quarantined_table"
                    if item.grid_status == "quarantined"
                    else "table_context_uncertain",
                    disposition="quarantine"
                    if item.grid_status == "quarantined"
                    else "retain_with_warning",
                )
            )
    return rows


def xbrl_rows(result: NormalizedFacts) -> Rows:
    result = NormalizedFacts.model_validate(result.model_dump())
    company = result.company
    assert company.id is not None
    rows: Rows = {
        "silver_companies": [company],
        "silver_provenance": [result.provenance],
        "silver_xbrl_facts": [r.fact for r in result.observations if r.fact is not None],
        "silver_xbrl_occurrences": [
            SourceOccurrence(
                pipeline_version=PIPELINE,
                company_id=company.id,
                source=company.source,
                occurrence=r,
            )
            for r in result.observations
        ],
        "silver_xbrl_concepts": [
            SourceConcept(
                pipeline_version=PIPELINE,
                company_id=company.id,
                source=company.source,
                metadata=c,
            )
            for c in result.concepts
        ],
        "silver_parse_quality": [],
    }
    counts = Counter(f.observation_id for f in typed(rows, "silver_xbrl_facts", FinancialFact))
    for occurrence in typed(rows, "silver_xbrl_occurrences", SourceOccurrence):
        value = occurrence.occurrence
        assert occurrence.id is not None
        reasons = list(value.reasons)
        if value.fact is not None and counts[value.fact.observation_id] > 1:
            reasons.append("duplicate_logical_observation")
        # One event per occurrence; all detailed upstream reasons remain in the occurrence.
        if value.quality != "passed" or reasons:
            rows["silver_parse_quality"].append(
                QualityEvent(
                    pipeline_version=PIPELINE,
                    entity_id=occurrence.id,
                    source=company.source,
                    rule="source_observation",
                    rule_version=PIPELINE,
                    state=value.quality if value.quality != "passed" else "warning",
                    reason_code="rejected_observation"
                    if value.fact is None
                    else (
                        "duplicate_logical_observation"
                        if "duplicate_logical_observation" in reasons
                        else "observation_semantics_unverified"
                    ),
                    disposition="quarantine" if value.fact is None else "retain_with_warning",
                )
            )
    return rows


def validate_silver(rows: Rows, versions: ProcessingVersions) -> None:
    """Reconstruct upstream envelopes and compare every canonical projection."""
    sources = typed(rows, "silver_sources", SourceEntry)
    if not sources or len({s.source for s in sources}) != 1:
        raise DatasetError("inconsistent_partition_sources")
    source = sources[0].source
    kind = source.source.kind
    names = HTML_DATASETS if kind == "filing" else XBRL_DATASETS if kind == "company_facts" else ()
    if set(rows) != {"silver_sources", *names}:
        raise DatasetError("incomplete_silver_partition")
    if not names:
        return
    for name, values in rows.items():
        for row in values:
            row = type(row).model_validate(row.model_dump())
            if hasattr(row, "source") and row.source != source:
                raise DatasetError("missing_or_inconsistent_source")
            if name not in {"silver_sources"} and row.pipeline_version not in {
                PIPELINE,
                "html-1",
                "xbrl-1",
                versions.tables,
            }:
                raise DatasetError("incompatible_processing_version")
    provenance = typed(rows, "silver_provenance", SourceProvenance)
    if {p.fetch_id for p in provenance} != {s.fetch.id for s in sources} or len(provenance) != len(
        sources
    ):
        raise DatasetError("incomplete_fetch_lineage")
    if kind == "filing":
        docs = typed(rows, "silver_documents", DocumentVersion)
        filings = typed(rows, "silver_filings", CanonicalFiling)
        metadata = typed(rows, "silver_parse_metadata", ParseMetadata)
        if len(docs) != 1 or len(filings) != 1 or len(metadata) != 1:
            raise DatasetError("invalid_document_cardinality")
        doc, meta = docs[0], metadata[0]
        if doc.parser_version != versions.parser or meta.classifier_version != versions.classifier:
            raise DatasetError("incompatible_parser_version")
        if meta.document_id != doc.id:
            raise DatasetError("orphan_parse_metadata")
        parsed = ParsedDocument(
            classifier_version=meta.classifier_version,
            encoding=meta.encoding,
            document=doc,
            filing=filings[0],
            sections=tuple(
                sorted(typed(rows, "silver_sections", Section), key=lambda s: s.ordinal)
            ),
            blocks=tuple(
                sorted(typed(rows, "silver_content_blocks", ContentBlock), key=lambda b: b.ordinal)
            ),
            provenance=provenance[0],
            quality_events=tuple(
                q
                for q in typed(rows, "silver_parse_quality", QualityEvent)
                if q.pipeline_version == "html-1"
            ),
        )
        details = typed(rows, "silver_table_details", TableDetail)
        texts = typed(rows, "silver_table_text", TableRepresentation)
        if any(d.document_id != doc.id for d in details) or any(
            t.document_id != doc.id for t in texts
        ):
            raise DatasetError("orphan_table_metadata")
        # Source traversal order is numeric DOM order, not lexicographic ID order.
        details.sort(
            key=lambda d: tuple(
                int(p.split("[")[1][:-1]) for p in d.extraction.locator.path.split("/")[1:]
            )
        )
        order = {
            d.extraction.table.id: i
            for i, d in enumerate(details)
            if d.extraction.table is not None
        }
        texts.sort(key=lambda t: order.get(t.representation.table_id, -1))
        tables = TableExtraction(
            document=doc,
            sections=parsed.sections,
            blocks=parsed.blocks,
            tables=tuple(d.extraction for d in details),
            retrieval=tuple(t.representation for t in texts),
        )
        expected = html_rows(parsed, tables)
    else:
        companies = typed(rows, "silver_companies", Company)
        if len(companies) != 1:
            raise DatasetError("invalid_company_cardinality")
        occurrences = typed(rows, "silver_xbrl_occurrences", SourceOccurrence)
        concepts = typed(rows, "silver_xbrl_concepts", SourceConcept)
        if any(r.company_id != companies[0].id for r in occurrences) or any(
            c.company_id != companies[0].id for c in concepts
        ):
            raise DatasetError("orphan_xbrl_metadata")
        normalized = NormalizedFacts(
            company=companies[0],
            provenance=provenance[0],
            observations=tuple(o.occurrence for o in occurrences),
            concepts=tuple(c.metadata for c in concepts),
        )
        expected = xbrl_rows(normalized)
    for name, values in expected.items():
        if name != "silver_provenance" and not same(rows[name], values):
            raise DatasetError("invalid_silver_projection")
    base = provenance[0]
    for p in provenance:
        entry = next(s for s in sources if s.fetch.id == p.fetch_id)
        if p != SourceProvenance.model_validate(
            {
                **base.model_dump(exclude={"id", "fetch_id", "fetched_at"}),
                "fetch_id": entry.fetch.id,
                "fetched_at": entry.fetch.fetched_at,
            }
        ):
            raise DatasetError("invalid_fetch_provenance")


def gold_rows(silver: Rows) -> Rows:
    """Gold consumes persisted Silver, never reinterprets Bronze or table amounts."""
    source = typed(silver, "silver_sources", SourceEntry)[0].source
    rows: Rows = {}
    if source.source.kind == "filing":
        rows = {name: [] for name in GOLD_HTML}
        sections = {s.id: s for s in typed(silver, "silver_sections", Section)}
        for block in typed(silver, "silver_content_blocks", ContentBlock):
            assert block.id is not None and block.section_id is not None
            section = sections[block.section_id]
            evidence = ResearchEvidence(
                pipeline_version=PIPELINE,
                document_id=block.document_id,
                section_id=block.section_id,
                block_id=block.id,
                ordinal=block.ordinal,
                kind=block.kind,
                text=block.text,
                text_sha256=block.text_sha256,
                section_classification=section.classification,
                quality="warning",
                source=source,
                locator=block.locator,
            )
            rows["gold_research_evidence"].append(evidence)
            rows["gold_citations"].append(
                citation(evidence, "gold_research_evidence", block, source, block.locator)
            )
        rows["gold_tables"] = list(silver["silver_tables"])
        rows["gold_table_text"] = list(silver["silver_table_text"])
        tables = {t.id: t for t in typed(silver, "silver_tables", StructuredTable)}
        for table in tables.values():
            rows["gold_citations"].append(
                citation(table, "gold_tables", table, source, table.locator)
            )
        for representation in typed(silver, "silver_table_text", TableRepresentation):
            table = tables[representation.representation.table_id]
            rows["gold_citations"].append(
                citation(representation, "gold_table_text", table, source, table.locator)
            )
    elif source.source.kind == "company_facts":
        rows = {name: [] for name in GOLD_XBRL}
        for fact in typed(silver, "silver_xbrl_facts", FinancialFact):
            if supported_fact(fact):
                rows["gold_reported_facts"].append(fact)
                rows["gold_citations"].append(
                    citation(fact, "gold_reported_facts", fact, source, fact.locator)
                )
    return rows


def supported_fact(fact: FinancialFact) -> bool:
    return (
        fact.quality != "failed"
        and fact.unit == "USD"
        and fact.currency == "USD"
        and fact.form in {"10-K", "10-Q", "10-K/A", "10-Q/A"}
        and any(
            fact.period.kind == m.period_kind
            and any((fact.taxonomy, fact.concept) == (c.taxonomy, c.concept) for c in m.concepts)
            for m in METRICS
        )
    )


def citation(
    target: Record, dataset: str, origin: Record, source: SourceReference, locator: object
) -> Citation:
    return Citation.model_validate(
        {
            "pipeline_version": PIPELINE,
            "target_id": target.id,
            "target_dataset": dataset,
            "source_entity_id": origin.id,
            "source": source,
            "locator": locator,
            "quality": "warning",
        }
    )
