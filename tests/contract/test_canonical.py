"""WP3.1 contracts and hand-annotated examples, not a normalization pipeline."""

import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal, localcontext
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from sec_research.contracts.bronze import validated_source
from sec_research.contracts.canonical import (
    CANONICAL_MODELS,
    CanonicalFiling,
    Company,
    ContentBlock,
    DatasetObject,
    DatasetPublication,
    DocumentVersion,
    FinancialFact,
    MetricDefinition,
    QualityEvent,
    Record,
    ReportingPeriod,
    ResearchChunk,
    Section,
    SourceLocator,
    SourceProvenance,
    SourceReference,
    StructuredTable,
    TableCell,
    stable_id,
)
from sec_research.contracts.schemas import schema_bundle, storage_row
from sec_research.contracts.sec import Filing, Source
from sec_research.ingestion.payloads import json_object, validate_payload
from sec_research.ingestion.ports import Fetch

FIXTURES = Path(__file__).parents[1] / "fixtures" / "canonical"
ROOT = Path(__file__).parents[2]
NOW = datetime(2026, 10, 20, tzinfo=UTC)
PIPELINE = "phase3-contracts-1"


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def rid(record: Record) -> str:
    assert record.id is not None
    return record.id


def fetch_fixture(filename: str = "annual.htm") -> tuple[Fetch, bytes]:
    manifest = json.loads((FIXTURES / "manifest.json").read_bytes())
    entry = next(item for item in manifest["fixtures"] if item["path"] == filename)
    source = Source.model_validate(entry["source"])
    body = (FIXTURES / filename).read_bytes()
    fetch = Fetch(
        id=UUID(int=1),
        run_id=UUID(int=2),
        source=source,
        sha256=entry["sha256"],
        storage_uri=f"file:///synthetic/bronze/sha256/{entry['sha256']}",
        manifest_uri="file:///synthetic/bronze/manifests/00000000000000000000000000000001.json",
        fetched_at=NOW,
        byte_count=entry["byte_count"],
        http_status=200,
        media_type="application/json" if filename.endswith(".json") else "text/html",
        attempts=1,
    )
    return fetch, body


def ref(filename: str = "annual.htm") -> SourceReference:
    return validated_source(*fetch_fixture(filename))


def record_examples() -> tuple[Record, ...]:
    source = ref()
    assert source.source.filing is not None
    company = Company(
        pipeline_version=PIPELINE,
        cik="0000000001",
        legal_name="Synthetic Example Research Corp",
        source=ref("company_facts.json"),
        fiscal_year_end="1228",
    )
    filing = CanonicalFiling(
        pipeline_version=PIPELINE,
        filing=source.source.filing,
        source=source,
    )
    document = DocumentVersion(
        pipeline_version=PIPELINE,
        filing_id=rid(filing),
        source=source,
        filename="annual.htm",
        role="primary",
        parser_version="fixture-1",
    )
    locator = SourceLocator(kind="dom", path="/html/body/p[1]")
    section = Section(
        pipeline_version=PIPELINE,
        document_id=rid(document),
        form="10-K",
        part="I",
        item="1",
        classification="classified",
        heading="Item 1. Business",
        ordinal=0,
        locator=locator,
        first_block_ordinal=0,
        last_block_ordinal=1,
        quality="passed",
    )
    text = "We manufacture synthetic widgets."
    block = ContentBlock(
        pipeline_version=PIPELINE,
        document_id=rid(document),
        section_id=rid(section),
        kind="paragraph",
        ordinal=1,
        text=text,
        text_sha256=digest(text.encode()),
        locator=locator,
    )
    table_block = ContentBlock(
        pipeline_version=PIPELINE,
        document_id=rid(document),
        section_id=None,
        kind="table",
        ordinal=10,
        text="",
        text_sha256=digest(b""),
        locator=SourceLocator(kind="dom", path="/html/body/table[1]"),
    )
    table = StructuredTable(
        pipeline_version=PIPELINE,
        document_id=rid(document),
        section_id=None,
        block_id=rid(table_block),
        locator=table_block.locator,
        rows=4,
        columns=3,
        title="Selected synthetic results",
        unit_hints=("USD",),
        scale_hint=Decimal("1000000"),
        footnotes=("(a) Includes synthetic restructuring expense.",),
        retrieval_text="Operating income; December 28, 2024; (25.50) USD millions (a)",
        quality="warning",
    )
    cell = TableCell(
        pipeline_version=PIPELINE,
        table_id=rid(table),
        row=3,
        column=1,
        is_header=False,
        raw_text="(25.50)",
        display_text="(25.50)",
        value=Decimal("-25.50"),
        numeric_status="parsed",
        footnote_markers=("(a)",),
        locator=SourceLocator(kind="dom", path="/html/body/table[1]/tr[4]/td[1]"),
    )
    fact = fact_example()
    provenance = SourceProvenance(
        pipeline_version=PIPELINE,
        entity_id=rid(block),
        source=source,
        locator=locator,
        fetch_id=UUID(int=1),
        fetched_at=NOW,
        input_entity_ids=(rid(document),),
    )
    chunk = ResearchChunk(
        pipeline_version=PIPELINE,
        document_id=rid(document),
        section_id=rid(section),
        source_block_ids=(rid(block),),
        ordinal=0,
        kind="narrative",
        text=text,
        text_sha256=block.text_sha256,
        token_count=5,
        tokenizer_version="fixture-word-count-1",
        chunker_version="fixture-1",
        source=source,
    )
    metric = MetricDefinition(
        pipeline_version=PIPELINE,
        metric_name="revenue",
        metric_version="fixture-1",
        description="Illustrative contract; no approved concept mapping.",
        mapping_status="unsupported",
        period_kind="duration",
        unit="USD",
        context_requirement="verified_consolidated",
        selection_policy_version="proposed-1",
        sign_policy="preserve",
        denominator_policy="not_applicable",
        rounding_policy="none",
        limitations=("Mapping approval belongs to WP3.4.",),
    )
    quality = QualityEvent(
        pipeline_version=PIPELINE,
        entity_id=rid(fact),
        rule="context_available",
        rule_version="1",
        state="warning",
        reason_code="context_unknown",
        disposition="retain_with_warning",
        source=fact.source,
    )
    publication = DatasetPublication(
        pipeline_version=PIPELINE,
        dataset_version="fixture-1",
        layer="silver",
        code_revision="synthetic",
        config_sha256=digest(b"config"),
        parser_version="fixture-1",
        input_source_sha256s=(source.sha256,),
        objects=(
            DatasetObject(
                dataset="silver_documents",
                path="silver/documents/part-0.parquet",
                sha256=digest(b"hypothetical-file"),
                row_count=1,
                schema_sha256=digest(b"schema"),
            ),
        ),
        state="staged",
        quality="warning",
        quality_event_ids=(rid(quality),),
    )
    return (
        company,
        filing,
        document,
        section,
        block,
        table,
        cell,
        fact,
        provenance,
        chunk,
        metric,
        quality,
        publication,
    )


def fact_example(**updates: object) -> FinancialFact:
    values: dict[str, object] = {
        "pipeline_version": PIPELINE,
        "cik": "0000000001",
        "taxonomy": "us-gaap",
        "concept": "RevenueFromContractWithCustomerExcludingAssessedTax",
        "raw_value": "1234500000.1250000001",
        "value": Decimal("1234500000.1250000001"),
        "unit": "USD",
        "currency": "USD",
        "period": ReportingPeriod(
            kind="duration",
            start=date(2023, 12, 31),
            end=date(2024, 12, 28),
            duration_class="unknown",
        ),
        "accession": "0000000001-25-000001",
        "form": "10-K",
        "filed": date(2025, 2, 1),
        "fy": 2024,
        "fp": "FY",
        "frame": "CY2024",
        "context_status": "unknown",
        "source": ref("company_facts.json"),
        "locator": SourceLocator(
            kind="json_pointer",
            path="/facts/us-gaap/RevenueFromContractWithCustomerExcludingAssessedTax/units/USD/0",
        ),
        "normalizer_version": "fixture-1",
        "quality": "warning",
    }
    return FinancialFact.model_validate(values | updates)


@pytest.mark.parametrize("model", CANONICAL_MODELS, ids=lambda model: model.__name__)
def test_all_record_families_round_trip_and_have_storage_schema(model: type[Record]) -> None:
    record = next(record for record in record_examples() if type(record) is model)
    encoded = storage_row(record)
    assert model.model_validate_json(encoded) == record
    assert json.loads(encoded)["schema_version"] == "canonical-1"
    assert rid(record).startswith(f"{model.namespace}:")
    schema = model.model_json_schema(mode="serialization")
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == "canonical-1"


def test_checked_in_schemas_match_implementation() -> None:
    assert json.loads((ROOT / "docs/schemas/canonical-1.json").read_bytes()) == schema_bundle()


@pytest.mark.parametrize(
    "filename", ["annual.htm", "quarter.htm", "malformed.htm", "company_facts.json"]
)
def test_fixtures_match_inventory_and_phase2_envelopes(filename: str) -> None:
    fetch, body = fetch_fixture(filename)
    assert fetch.sha256 == digest(body)
    assert fetch.byte_count == len(body)
    validate_payload(fetch.source, body, fetch.media_type)
    source = validated_source(Fetch.model_validate_json(fetch.model_dump_json()), body)
    assert source.source == fetch.source
    assert source.sha256 == fetch.sha256


def test_existing_phase2_fixtures_remain_compatible() -> None:
    existing = FIXTURES.parent / "sec"
    inventory = json.loads((existing / "manifest.json").read_bytes())
    for entry in inventory["fixtures"]:
        body = (existing / entry["path"]).read_bytes()
        assert digest(body) == entry["sha256"] and len(body) == entry["byte_count"]
    fetch, _ = fetch_fixture()
    body = (existing / "filing.htm").read_bytes()
    data = fetch.model_dump() | {"sha256": digest(body), "byte_count": len(body)}
    reference = validated_source(Fetch.model_validate(data), body)
    assert reference.source.filing == fetch.source.filing


@pytest.mark.parametrize(
    "change",
    [
        {"sha256": "0" * 64},
        {"byte_count": 0},
        {"processing_status": "quarantined"},
        {"fetched_at": datetime(2026, 10, 20)},
    ],
)
def test_bronze_boundary_rejects_ineligible_sources(change: dict[str, object]) -> None:
    fetch, body = fetch_fixture()
    with pytest.raises(ValueError):
        validated_source(Fetch.model_validate(fetch.model_dump() | change), body)


def test_repeated_fetch_preserves_artifact_identity_and_separate_fetch_lineage() -> None:
    fetch, body = fetch_fixture()
    later = Fetch.model_validate(
        fetch.model_dump() | {"id": UUID(int=3), "fetched_at": "2026-10-21T00:00:00Z"}
    )
    assert validated_source(fetch, body) == validated_source(later, body)
    first = next(x for x in record_examples() if isinstance(x, SourceProvenance))
    second = SourceProvenance.model_validate(
        first.model_dump(exclude={"id"}) | {"fetch_id": later.id, "fetched_at": later.fetched_at}
    )
    assert first.id != second.id


def test_identifiers_are_order_independent_and_version_sensitive() -> None:
    assert stable_id("test", {"a": 1, "b": "é"}) == stable_id("test", {"b": "é", "a": 1})
    # Golden vector freezes id-1 encoding; changing it requires an explicit identity migration.
    assert stable_id("test", {"a": 1}) == (
        "test:ed5547b91ce5a3a21b88ff4295b6c0555f8b15d1b38096c726b722f6b39ed318"
    )
    fact = fact_example()
    assert fact.id == fact_example().id
    assert fact.id != fact_example(normalizer_version="fixture-2").id
    assert fact.id != fact_example(pipeline_version="phase3-contracts-2").id
    with pytest.raises(ValueError):
        stable_id("invalid:namespace", {})
    with pytest.raises(ValidationError, match="record ID"):
        FinancialFact.model_validate(fact.model_dump() | {"normalizer_version": "changed"})


@pytest.mark.parametrize("value", [1.1, True, "NaN", "Infinity", "-Infinity"])
def test_financial_values_reject_float_bool_and_nonfinite(value: object) -> None:
    with pytest.raises(ValidationError):
        fact_example(value=value)


def test_decimal_preserves_precision_and_is_independent_of_decimal_context() -> None:
    with localcontext() as context:
        context.prec = 6
        fact = fact_example()
        encoded = storage_row(fact)
        assert json.loads(encoded)["value"] == "1234500000.1250000001"
        assert fact.value == Decimal("1234500000.1250000001")
        identity = fact.observation_id
    assert identity == fact_example().observation_id
    assert (
        fact_example(raw_value="1.0", value=Decimal("1.0")).observation_id
        == fact_example(raw_value="1.00", value=Decimal("1.00")).observation_id
    )


def test_occurrences_later_reportings_and_changed_values_remain_distinct() -> None:
    original = fact_example()
    duplicate = fact_example(
        locator=SourceLocator(
            kind="json_pointer",
            path="/facts/us-gaap/RevenueFromContractWithCustomerExcludingAssessedTax/units/USD/1",
        )
    )
    assert original.id != duplicate.id
    assert original.observation_id == duplicate.observation_id
    comparative = fact_example(
        accession="0000000001-26-000001",
        filed=date(2026, 2, 1),
        fy=2025,
    )
    assert original.observation_id != comparative.observation_id
    assert original.period == comparative.period
    changed = fact_example(
        raw_value="1234600000.1250000001", value=Decimal("1234600000.1250000001")
    )
    assert original.observation_id != changed.observation_id


@pytest.mark.parametrize(
    "changes",
    [
        {"kind": "instant", "start": date(2024, 1, 1), "end": date(2024, 1, 2)},
        {"kind": "instant", "end": date(2024, 1, 2), "duration_class": "annual"},
        {"kind": "duration", "end": date(2024, 1, 2), "duration_class": "unknown"},
        {
            "kind": "duration",
            "start": date(2024, 2, 1),
            "end": date(2024, 1, 2),
            "duration_class": "unknown",
        },
        {
            "kind": "duration",
            "start": date(2024, 1, 1),
            "end": date(2024, 12, 31),
            "duration_class": "annual",
        },
    ],
)
def test_invalid_measurement_periods_fail(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ReportingPeriod.model_validate(changes)


@pytest.mark.parametrize(
    ("start", "end", "classification", "days"),
    [
        ("2024-03-31", "2024-06-29", "quarter", 91),
        ("2023-12-31", "2024-06-29", "year_to_date", 182),
        ("2023-12-31", "2024-12-28", "annual", 364),
        ("2022-12-25", "2023-12-30", "annual", 371),
        ("2024-01-01", "2024-12-31", "annual", 366),
    ],
)
def test_actual_measurement_dates_support_fiscal_intervals(
    start: str,
    end: str,
    classification: str,
    days: int,
) -> None:
    period = ReportingPeriod.model_validate(
        {
            "kind": "duration",
            "start": start,
            "end": end,
            "duration_class": classification,
            "classification_policy": "hand-annotated-fixture-1",
        }
    )
    assert period.start is not None
    assert (period.end - period.start).days + 1 == days
    assert fact_example(period=period, fy=2025).period == period


@pytest.mark.parametrize(
    "changes",
    [
        {"raw_value": "12"},
        {"currency": "EUR"},
        {"dimensions": ()},
        {"context_id": "invented"},
        {"context_status": "verified"},
        {"filed": date(2024, 1, 1)},
        {"cik": "1"},
        {"cik": "0000000000"},
        {"source": ref()},
        {"accepted_at": datetime(2025, 2, 1)},
        {"extra_field": "silently ignored?"},
        {"schema_version": "canonical-2"},
    ],
)
def test_fact_semantic_failures(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        fact_example(**changes)


def test_unknown_context_and_instant_are_explicit() -> None:
    fact = fact_example()
    assert fact.context_status == "unknown" and fact.dimensions is None
    verified = fact_example(context_status="verified", dimensions=())
    assert verified.observation_id != fact.observation_id
    instant = fact_example(
        concept="Assets",
        raw_value="2500000000",
        value=Decimal("2500000000"),
        period=ReportingPeriod(kind="instant", end=date(2024, 12, 28)),
    )
    assert instant.period.start is None and instant.period.duration_class is None


@pytest.mark.parametrize(
    "values",
    [
        {"kind": "dom", "path": "relative"},
        {"kind": "json_pointer", "path": "/units/USD~2shares"},
        {"kind": "dom", "path": "/p[1]", "start": 0},
        {"kind": "dom", "path": "/p[1]", "start": 3, "end": 2, "text_sha256": "a" * 64},
        {"kind": "json_pointer", "path": "/val", "start": 0, "end": 1, "text_sha256": "a" * 64},
    ],
)
def test_locator_failures(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        SourceLocator.model_validate(values)


def test_locators_preserve_normalized_offsets_and_escaped_unit_pointer() -> None:
    locator = SourceLocator(kind="dom", path="/p[1]", start=0, end=3, text_sha256=digest(b"abc"))
    assert locator.end == 3
    assert SourceLocator(kind="json_pointer", path="/units/USD~1shares/0").path.endswith("/0")


@pytest.mark.parametrize(
    ("model", "changes"),
    [
        (Company, {"fiscal_year_end": "1331"}),
        (CanonicalFiling, {"amends_accession": "0000000001-24-000001"}),
        (DocumentVersion, {"filename": "other.htm"}),
        (Section, {"first_block_ordinal": 3}),
        (Section, {"classification": "ambiguous"}),
        (Section, {"form": "10-Q", "part": None}),
        (ContentBlock, {"text": "changed"}),
        (StructuredTable, {"scale_hint": Decimal("-1")}),
        (TableCell, {"row_span": 0}),
        (TableCell, {"numeric_status": "uncertain"}),
        (TableCell, {"numeric_status": "empty", "value": None}),
        (ResearchChunk, {"text": "changed"}),
        (ResearchChunk, {"source_block_ids": ()}),
        (ResearchChunk, {"kind": "table"}),
        (MetricDefinition, {"mapping_status": "supported"}),
        (MetricDefinition, {"limitations": ()}),
        (QualityEvent, {"state": "failed"}),
        (DatasetPublication, {"state": "published"}),
        (DatasetPublication, {"published_at": NOW}),
    ],
)
def test_record_invariants(model: type[Record], changes: dict[str, object]) -> None:
    record = next(x for x in record_examples() if type(x) is model)
    with pytest.raises(ValidationError):
        model.model_validate(record.model_dump(exclude={"id"}) | changes)


def test_unclassified_sections_and_uncertain_cells_preserve_source_text() -> None:
    section = next(x for x in record_examples() if isinstance(x, Section))
    unknown = Section.model_validate(
        section.model_dump(exclude={"id"})
        | {
            "classification": "unclassified",
            "item": None,
            "quality": "warning",
        }
    )
    assert unknown.heading == section.heading and unknown.locator == section.locator
    cell = next(x for x in record_examples() if isinstance(x, TableCell))
    uncertain = TableCell.model_validate(
        cell.model_dump(exclude={"id"})
        | {
            "numeric_status": "uncertain",
            "value": None,
        }
    )
    assert uncertain.raw_text == "(25.50)" and uncertain.value is None


@pytest.mark.parametrize(
    "path",
    [
        "../x.parquet",
        "/x.parquet",
        "C:/x.parquet",
        "a\\x.parquet",
        "a//x.parquet",
        "a/./x.parquet",
        "x.json",
    ],
)
def test_dataset_paths_are_relative_and_safe(path: str) -> None:
    with pytest.raises(ValidationError):
        DatasetObject(dataset="x", path=path, sha256="a" * 64, row_count=0, schema_sha256="b" * 64)


def test_publication_contract_checks_order_quality_and_timestamps() -> None:
    staged = next(x for x in record_examples() if isinstance(x, DatasetPublication))
    fields = staged.model_dump(exclude={"id"})
    published = DatasetPublication.model_validate(
        fields
        | {
            "state": "published",
            "validated_at": NOW,
            "published_at": NOW,
        }
    )
    assert published.id != staged.id
    invalid_changes: list[dict[str, object]] = [
        {"objects": (*staged.objects, *staged.objects)},
        {"input_source_sha256s": ("b" * 64, "a" * 64)},
        {"state": "validated", "validated_at": NOW, "quality": "failed"},
        {"state": "published", "validated_at": NOW, "published_at": "2025-01-01T00:00:00Z"},
    ]
    for changes in invalid_changes:
        with pytest.raises(ValidationError):
            DatasetPublication.model_validate(fields | changes)


def test_storage_boundary_rejects_bypassed_validation() -> None:
    fact = fact_example().model_copy(update={"value": Decimal("1")})
    with pytest.raises(ValidationError):
        storage_row(fact)


def test_fixture_json_values_are_decimal_and_expected_observations_survive() -> None:
    body = (FIXTURES / "company_facts.json").read_bytes()
    data = json.loads(body, parse_float=Decimal)
    # Phase 2's existing envelope reader must preserve the same values.
    assert json_object(body) == data
    revenues = data["facts"]["us-gaap"]["RevenueFromContractWithCustomerExcludingAssessedTax"]
    rows = revenues["units"]["USD"]
    assert len(rows) == 7 and rows[0] == rows[1]
    assert rows[0]["val"] == Decimal("1234500000.1250000001")
    assert rows[2]["fy"] == 2025 and rows[2]["end"] == rows[0]["end"]
    assert rows[3]["start"] != rows[4]["start"] and rows[3]["fp"] == rows[4]["fp"]
    assert rows[6]["start"] > rows[6]["end"]
    assert "EUR" in revenues["units"]
    assert "start" not in data["facts"]["us-gaap"]["Assets"]["units"]["USD"][0]


def test_canonical_filing_reuses_phase2_metadata_without_loss() -> None:
    filing = Filing(
        cik="1",
        accession="000000000126000001",
        form="10-Q",
        filing_date=date(2026, 8, 1),
        report_date=date(2026, 6, 27),
        accepted_at=NOW,
        primary_document="quarter.htm",
    )
    source = Source(kind="filing", cik=filing.cik, filing=filing, url=filing.source_url)
    record = CanonicalFiling(
        pipeline_version=PIPELINE,
        filing=filing,
        source=SourceReference(source=source, sha256="a" * 64, byte_count=1),
    )
    assert record.filing == filing
    assert record.filing.cik == "0000000001"
    assert record.filing.accession == "0000000001-26-000001"
    assert record.filing.report_date != record.filing.filing_date
