# Data dictionary and contract invariants

Status: Phase 2 company/filing/source/fetch contracts and ingestion SQL records are implemented; see [ingestion](ingestion.md). Silver/Gold, financial and research records below remain proposed logical contracts. Physical schemas, indexes, migrations, and exact field constraints are assigned to their delivery packages. All external contracts carry a `schema_version`.

WP3.1 implements the canonical record subset and portable storage-row schemas
specified in [canonical contracts](canonical-contracts.md). That document
distinguishes validated fields from future cross-row checks and physical adapters.
The broader projections, selection/calculation services and research records below
remain proposed; no Silver/Gold dataset has been produced by WP3.1.

## Shared conventions

- CIK: ten-digit zero-padded string, never a ticker or integer display key. Accessions retain canonical dashed form and a separately derived archive path form.
- Dates: ISO `YYYY-MM-DD`; timestamps: timezone-aware UTC. Store date-only availability as date-only with a precision flag; do not fabricate an acceptance time.
- Numeric facts: decimal lexical strings in JSON/Parquet contracts, Decimal in application calculations, exact SQL numeric or preserved text where source precision exceeds a chosen numeric column. Never coerce through binary float.
- IDs: artifact IDs are SHA-256; dataset/evidence/chunk IDs derive from versioned canonical identity inputs or a recorded build identity. UUIDs identify operational runs/jobs. Hash serialization and field ordering are versioned and deterministic.
- Null means unknown/not supplied, not zero, empty dimensions, or negative evidence. Use explicit status enums for missing, ambiguous, invalid, quarantined, and unsupported outcomes.
- Relationships reference stable IDs and snapshot/schema versions. Database constraints and publication checks enforce referential integrity; foreign keys alone cannot validate object-store existence.

## Core records

| Record | Key fields and types | Identity and invariants |
| --- | --- | --- |
| `Company` | `cik: str`, `legal_name: str`, `sic: str?`, `fiscal_year_end: str?`, `source_artifact_id` | CIK identity; no uniqueness assumption on name |
| `CompanyAlias` | `cik`, `alias_type`, `value`, `valid_from?`, `valid_to?`, `source_artifact_id` | Ticker/exchange/name history with unknown intervals explicit |
| `Filing` | `cik`, `accession`, `form`, `filing_date`, `accepted_at?`, `report_date?`, `primary_document`, `source_url`, `amends_accession?` | Unique accession identity; amendment links require evidence; availability separate from measurement period |
| `Artifact` | `artifact_id`, `sha256`, `storage_key`, `media_type`, `byte_count`, `encoding?` | Immutable bytes; hash and length must verify on read/reconciliation |
| `FetchManifest` | `manifest_id`, `artifact_id?`, `source_url`, `source_kind`, `fetched_at`, `status`, `http_status?`, `etag?`, `last_modified?`, `ingestion_run_id` | Successful status requires artifact; failed attempts retain diagnostics without source-byte claims |
| `Document` | `document_id`, `accession`, `artifact_id`, `role`, `parser_version`, `text_hash` | Distinct source document and parser rendition; filing can have multiple documents |
| `Section` | `section_id`, `document_id`, `parent_section_id?`, `label?`, `heading`, `ordinal`, `locator`, `confidence` | Ordered hierarchy; heuristic label/confidence not asserted as exact source truth |
| `ContentBlock` | `block_id`, `section_id?`, `document_id`, `kind`, `ordinal`, `text`, `text_hash`, `locator` | Kind: paragraph, heading, list, table; mapping resolves to original artifact |
| `FinancialTable` | `table_id`, `block_id`, `headers`, `cells`, `footnotes`, `unit_hints`, `scale_hints`, `quality_status` | Preserve row/column and span structure; unknown scale cannot silently become 1 |
| `TableCell` | `table_id`, `row`, `column`, `row_span`, `column_span`, `raw_text`, `normalized_value?`, `header_refs`, `locator` | Source cell retained even if numeric normalization fails |
| `Concept` | `taxonomy`, `name`, `label?`, `description?`, `period_type?`, `source_artifact_id` | Taxonomy/name identify a concept; similar labels do not prove equivalence |
| `ReportingPeriod` | `period_id`, `kind`, `start?`, `end`, `calendar_label?`, `fiscal_label?`, `duration_days?` | `instant` has no start; `duration` requires start ≤ end; fiscal label derived under a recorded policy |

## XBRL observation

Each `FinancialObservation` preserves:

| Field | Type and meaning |
| --- | --- |
| `observation_id` | Stable ID for source reporting/context/value identity; duplicate ingestion cannot create a new logical fact |
| `cik`, `taxonomy`, `concept` | Issuer and source concept identity |
| `raw_value`, `value` | Source lexical numeric representation and exact normalized decimal string |
| `unit`, `currency?`, `scale_applied` | Canonical unit and explicit transformation; Company Facts values must not receive a table's scale again |
| `period_kind`, `period_start?`, `period_end` | Measurement interval or instant, independent of SEC filing fiscal metadata |
| `accession`, `form`, `filed`, `accepted_at?` | Reporting event and availability metadata |
| `fy?`, `fp?`, `frame?` | Preserved source metadata; not authoritative measurement-period selectors |
| `context_id?`, `dimensions?`, `context_status` | Raw XBRL context when available; status distinguishes verified context from unavailable context |
| `source_artifact_id`, `source_locator` | Raw Company Facts JSON pointer or raw XBRL locator with accession linkage |
| `schema_version`, `normalizer_version` | Reprocessing identity |
| `quality_status`, `quality_event_ids` | Validation eligibility and reasons |

Deduplicate exact logical observations without deleting their `ObservationSource` links to each immutable fetch artifact. A changed value, reporting accession, context, or period creates a distinct observation. Missing context fields remain unknown; an empty dimension set is reserved for verified absence of dimensions. Later filings may repeat the same value; retain their distinct reporting availability.

## Selection and calculation

| Contract | Fields | Required invariants |
| --- | --- | --- |
| `FactSelectionRequest` | CIK, metric/concepts, exact period constraints, unit/currency/context requirements, snapshot, `as_of`, selection mode, policy version | Model cannot override server scope or approved concept mapping |
| `FactSelectionResult` | Status, candidate IDs, selected IDs, rejected-candidate reasons, selection policy, availability precision, warnings | Success has enough verified inputs; ambiguity is explicit; ties never resolved by input order |
| `MetricDefinition` | Metric ID/version, approved concepts and priorities, period kind, unit/context rules, formula ID, denominator/sign/rounding policy | Semantics documented and versioned; capex exclusions explicit |
| `CalculationRecord` | Calculation ID, formula/version, input observation/calculation IDs, exact values/units, output, period alignment, display precision, policy version | Deterministic derivation; no circular input references; undefined results carry reason, never infinity/NaN |
| `FinancialComparison` | Input metric IDs, actual intervals, absolute change, relative change or percentage-point change, comparability status | Do not present unlike fiscal intervals as calendar-matched; currency/context must be compatible |

Financial observation eligibility and ranking are specified in [ADR-006](adr/ADR-006-financial-correctness.md). Selected facts retain rejected-candidate reasons so research can explain why a plausible alternative was not used.

## Research datasets and evidence

| Record | Key fields | Invariants |
| --- | --- | --- |
| `DatasetManifest` | Dataset ID/version, layer, input manifest IDs, code revision, schema/parser/config versions, object list/hashes, row counts, quality summary, build status | Only complete validated manifests are publishable; published manifest is immutable |
| `ResearchChunk` | Chunk ID, snapshot, document/section/block IDs, text/hash, token count/tokenizer, chunker version, metadata filters | Entire chunk resolves to source blocks; no evidence from another snapshot |
| `EvidenceRecord` | Evidence ID, snapshot, kind, source artifact ID/hash, accession, CIK, source URL, locator, excerpt/hash, availability | Kind distinguishes narrative/table/financial fact; source URL derives from registered SEC provenance |
| `SourceLocator` | Document identity and DOM/block/table coordinates, or JSON pointer/context identity; optional text offsets | Offsets refer to a named normalized representation; never label normalized offsets as raw-byte offsets |
| `EmbeddingRecord` | Chunk ID, index version, model ID, dimension, vector, content hash, generated_at | Dimension/model/chunk hash must match index contract |
| `QualityEvent` | Event ID, run/dataset/entity IDs, rule/version, severity, reason, source references, disposition | Hard integrity violations prevent publication; warnings retained for downstream use |
| `ObservationSource` | Observation ID, artifact ID, JSON/XBRL locator, fetch manifest ID | Many source snapshots may support the same logical observation |

For narrative evidence, resolve to the original SEC filing document and stable section/block locator, with a raw artifact checksum. For structured facts, preserve the API JSON pointer and accession link to the filing; do not claim an exact HTML table cell has been verified unless that mapping exists. Show the appropriate provenance level in the report.

## Operational and report contracts

`IngestionRun` and `ProcessingRun` record code/config versions, start/end times, input/output manifests, status, and safe failure details. `ResearchJob` records actor scope, idempotency key plus payload hash, request schema, snapshot, status, lease owner/expiry, attempts, and cancellation state. Terminal statuses cannot return to running without an explicit new attempt/recovery record.

`ResearchCheckpoint` carries run ID, graph/state schema versions, step, checkpoint sequence, validated state, and usage budgets. `ToolExecution` records validated arguments, versioned result references, elapsed time, retry reason, and safe error code. Avoid storing secrets or private hidden reasoning.

`ResearchReport` and claim/citation/calculation fields follow the [AI architecture](architecture/ai-architecture.md). Store original validated report versions and any later corrections separately. Claims can refer only to evidence/calculation IDs in the run's authorized snapshot or recorded deterministic derivation set.

## Evolution and compatibility

Validate external SEC payloads while retaining raw bytes and tolerating unknown source fields deliberately. A known field changing type must raise a contract/quality event. Internal contracts are stricter and independently versioned. Reprocessing under a new schema creates new dataset manifests; SQL migrations and API schema changes require compatibility tests. Delete neither historical observations nor report provenance to simplify a schema upgrade.
