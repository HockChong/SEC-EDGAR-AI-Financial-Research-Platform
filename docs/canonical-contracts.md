# WP3.1 canonical contracts

Architecture 3.1; contract version `canonical-1`; identity encoding `id-1`.
This package defines validated records and storage row schemas. It does not parse
HTML, normalize a Company Facts corpus, select metrics, produce datasets or
activate publications. Those remain WP3.2–3.7.

WP3.2 now consumes these unchanged canonical rows through the validated
`html-result-1` envelope. See [HTML parsing](html-parsing.md) for source graph,
normalized-offset, parser-version and failure contracts. It does not change
`canonical-1` storage schemas or implement physical dataset publication.

## Authority and compatibility

[ADR-003](adr/ADR-003-data-pipeline.md) remains authoritative: immutable Bronze,
versioned Parquet and manifests for Silver/Gold, PostgreSQL for coordination and
serving projections. No new dependency, database migration, Spark, Delta, parser,
tokenizer, embedding or agent is introduced.

The [existing ingestion contracts](../src/sec_research/contracts/sec.py) and
`ingestion.ports.Fetch` remain unchanged. Canonical records reuse the validated
Phase 2 `Source` and `Filing` metadata, including normalized ten-digit CIK, dashed
accession, primary filename, form, filing/report dates, original SEC URL and
optional acceptance timestamp. Canonical standalone CIK fields require the
already-normalized form; ingestion's existing normalization remains the entry point.

`contracts.bronze.validated_source(fetch, body)` revalidates the Phase 2 fetch,
rejects quarantine and naive fetch timestamps, and verifies byte count and SHA-256.
It returns an immutable `SourceReference`. The caller must obtain bytes through
the existing Bronze port and verify the stored manifest through reconciliation;
the bridge does not perform I/O, discover sources or interpret payload contents.
Hash validity proves byte integrity, not semantic correctness.

Fetch IDs/times are retained in separate `SourceProvenance` rows, not included in
artifact identity. Identical content fetched again can retain its canonical
identity while preserving every fetch relationship. Local storage paths are not
part of canonical content identities.

## Record families and datasets

The implementation is in [canonical.py](../src/sec_research/contracts/canonical.py).
All 13 record families inherit a frozen, extra-forbidding Pydantic record, carrying
`schema_version`, `pipeline_version` and a validated deterministic `id`.

- `Company` → `silver_companies`: CIK, legal name, optional SIC/fiscal-year-end,
  ticker aliases and source artifact. Alias history is not inferred.
- `CanonicalFiling` → `silver_filings`: original `Filing`, source and optional
  evidence-backed amendment link; amendment metadata cannot point to itself.
- `DocumentVersion` → `silver_documents`: filing row ID, filename, role, parser
  version, optional normalized text hash and exact source reference. This first
  contract accepts the primary-document coverage supplied by Phase 2. Exhibit
  ingestion requires a future explicit source-contract extension.
- `Section` → `silver_sections`: document/parent IDs, form/part/item, heading,
  order, inclusive first/last block ordinals, source locator and classification.
  Ambiguous/unclassified sections remain representable with warnings or failures.
- `ContentBlock` → `silver_content_blocks`: ordered heading, paragraph, list,
  table, footnote or other content; nullable section; verified UTF-8 text checksum.
- `StructuredTable` → `silver_tables`: source block/document/section, row/column
  counts, title, unit/scale hints, footnotes, retrieval text and quality state.
- `TableCell` → `silver_table_cells`: table, zero-based row/column, positive spans,
  header references, raw/display text, unit hints, footnotes, numeric status,
  optional exact value and DOM locator. Uncertain text survives without a value.
- `FinancialFact` → `silver_xbrl_facts`: taxonomy/concept, lexical/exact amount,
  unit/currency, actual period, filing availability, accession/form, `fy`/`fp`/frame,
  context uncertainty, source pointer, normalizer version and quality.
- `SourceProvenance` → `silver_provenance`: entity, source, locator, fetch ID/time
  and input entity IDs. Many source/fetch links can support one logical observation.
- `QualityEvent` → `silver_parse_quality`: entity, rule/version, reason code,
  source, `passed`/`warning`/`failed`, and matching disposition. Reason codes avoid
  arbitrary exception/log payloads; downstream quality evaluation remains future work.
- `ResearchChunk` → `gold_research_chunks`: document/section, ordered source
  blocks, related tables, text/hash, tokens, tokenizer/chunker versions and exact
  filing source. Table chunks require a structured table reference.
- `MetricDefinition`: versioned catalog contract for future Gold financial metric
  processing; approved mappings or registered formula identity, input metric IDs,
  selection/context/unit/sign/denominator/rounding policies, limitations.
  No concept catalog or formula execution is implemented in WP3.1.
- `DatasetPublication`: versioned manifest contract for either layer, code/config
  and processing versions, input hashes/manifests, Parquet object paths/checksums,
  row counts/schema hashes, state, quality references and validation/publication times.

Gold fact projections, metric results, timelines, company catalogs, chunk-source
projections and evidence-registry processing remain assigned to WP3.5–3.7. Their
future projections must reuse these identities rather than create another
authoritative store.

## Financial invariants

Financial amounts are `Decimal` in Python and decimal strings in serialized rows.
Floats, booleans and nonfinite numbers are rejected. `raw_value` preserves the
numeric lexical representation and must equal the canonical amount. No table scale
is applied to Company Facts values. A table's scale is an optional hint, never an
implicit multiplier or an assumed 1. A parsed table cell's value is its display
amount, without application of that hint.

`ReportingPeriod` requires an end date. An instant has no start or duration
classification; a duration requires ordered actual dates and explicit classification.
Quarter/YTD/annual/other labels require a classification-policy version. `unknown`
is supported before that policy exists. No validator derives a period from `fy`,
`fp`, frame, a fixed 365-day assumption or the filing date.

The fact's `filed` date is distinct from its measurement end and cannot precede it.
Optional canonical acceptance timestamps are explicitly zoned and normalized to
UTC. The nested Phase 2 source/filing metadata is preserved, including its original
zoned timestamp representation; no acceptance time is synthesized for date-only
sources. As-of selection and its end-of-day semantics belong to WP3.4.

Unknown context requires `dimensions=None` and `context_id=None`; it does not mean
consolidated. Verified context requires an explicit tuple of dimensions, with
unique axes sorted by name; an empty tuple means verified absence of dimensions.
The contract cannot itself verify external context evidence. Company Facts
coverage does not establish all custom taxonomy or dimensional facts.

## Identity and serialization

`id-1` hashes the UTF-8 encoding of `[identity_version, namespace, payload]` using
SHA-256. JSON uses sorted object keys, compact separators, unescaped Unicode and
no nonfinite values. Array order remains meaningful; no whitespace or Unicode
normalization is performed on source text. Record payloads contain every declared
field except `id`, including schema/pipeline and component versions. Supplied IDs
must match recomputation. Record IDs are `namespace:lowercase_sha256`.

Changing source identity, parser/normalizer/chunker version or canonical content
changes the record ID. A publication transition creates a new immutable manifest
record; `dataset_version` groups its build. Chunk IDs do not contain their eventual
publication ID, avoiding an identity cycle. Snapshot membership will be recorded
by publication/evidence mappings, not by mutating published chunk content.

A fact record identifies a particular source occurrence and rendition. The
`FinancialFact.observation_id` property separately identifies the logical reporting
using actual dates, company/concept, amount/unit/currency, reporting accession and
availability, and context. It excludes source JSON pointer/hash, fiscal labels,
frame and processing classifications. Equivalent decimal values have identical
logical IDs even if their lexical trailing zeros differ; original lexical text is
still preserved in the occurrence record. Changing a reporting accession or amount
changes the logical ID. Later reportings do not by themselves prove restatement.
The logical ID is derived on demand; occurrence `id` is the stored primary key.

`contracts.schemas.storage_row(record)` revalidates at the persistence boundary,
including objects created with Pydantic's validation-bypassing construction/copy
APIs, and emits deterministic UTF-8 JSON. Consumers must revalidate on read as well.
Frozen models are an application convention, not a security boundary.

## Storage schemas and deferred physical adapters

[canonical-1.json](schemas/canonical-1.json) contains the serialization JSON Schema
for each record family, generated by `contracts.schemas.schema_bundle()`. Stored
rows contain every field, including explicit nulls and the computed ID; the schema
declares them required. Pydantic additionally enforces cross-field invariants that
ordinary JSON Schema cannot express. A schema drift test guards the checked-in
bundle. To inspect/regenerate its content:

```bash
bash scripts/uv.sh run --frozen python -m sec_research.contracts.schemas
```

These are portable **storage-row schemas**, not a Parquet writer or SQL migration.
WP3.5 must bind them to explicit Arrow schemas: strings → UTF-8, Decimal → UTF-8
lexical decimal, dates → date32, canonical timestamps → UTC microseconds, bounded
integers → int64 with overflow rejection, booleans → bool, nested models → struct,
and tuples → lists with their element type. Optional fields stay nullable;
empty lists stay distinct from null. Do not infer types from a sample or allocate
an arbitrary fixed decimal precision/scale. Preserve original zoned timestamps
inside embedded Phase 2 metadata as strings.

Arrow physical schema metadata must record the contract and encoding versions.
`DatasetObject.schema_sha256` is the checksum of the canonical JSON encoding of its
record's serialization schema from this bundle. Future adapters must prove
lossless round trips against these records before publication. Adding Arrow now
would add a dependency before any physical dataset is produced; the existing
dependency lock remains unchanged.

Record-local validation is implemented here. Cross-row existence, namespace/type
matching of references, table-span overlap/bounds, section ownership, locator
resolution, source text completeness, published-object existence/checksums, actual
row counts, quarantine isolation and atomic activation require WP3.2–3.7. A
`state="published"` model passing validation does **not** prove those operations
occurred. State transitions and activation are not implemented by this package.

## Fixtures and verification

[The synthetic fixture inventory](../tests/fixtures/canonical/manifest.json) pins
four files and Phase 2-compatible source identities. Its [notes](../tests/fixtures/canonical/README.md)
describe deliberate malformed/uncertain cases and expected financial distinctions.
Fixtures contain no real issuer financial claims or downloaded source bodies.

Contract tests cover every record's serialization/schema, checksum compatibility,
deterministic/versioned identifiers, float/nonfinite rejection, precision, duplicate
occurrences, later reporting, fiscal intervals, context uncertainty, invalid
metadata, table/section/chunk constraints and manifest state/path constraints.
These are finite contract checks, not parser/normalizer accuracy or retrieval
benchmarks. See the [WP3.1 review](phase-3-wp3.1-review.md) for actual run results.
