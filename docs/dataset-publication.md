# WP3.5 Silver/Gold publication

Architecture 3.1 / ADR-003. `datasets-1` adds bounded Python/Arrow processing,
versioned Parquet, immutable manifests, and PostgreSQL snapshot activation.
The WP3.2–WP3.4 processors and canonical IDs are reused unchanged. No chunking,
embeddings, financial calculations, Spark, Delta, or AI frameworks are introduced.

## Contracts and lineage

`contracts/datasets.py` defines supplementary source, processing, observation,
evidence, citation, selection, and snapshot records. Existing canonical rows keep
their original pipeline versions and IDs. Supplementary records use `datasets-1`.
`processing/dataset_rows.py` implements pure projections and cross-row checks;
`processing/datasets.py` coordinates bounded source partitions through storage.

Silver contains companies, filings, documents, sections, content blocks, tables,
cells, parse metadata, table details/text, XBRL facts/occurrences/concepts, provenance,
quality events, and source entries. Original accessions, fetches, source URLs,
checksums, locators and processor versions survive. Repeated identical fetches
share canonical rows while retaining every fetch relationship. Reference-only
submissions/company metadata remain listed and checksum-verified, without a newly
invented metadata parser. Input scope comes from the explicit Bronze inventory.

Supplementary table details and XBRL occurrences deliberately also retain their
validated upstream envelope content. This duplicates canonical cells/facts on disk,
but permits exact cross-checks against normalized projections and retains raw
rejections, context, titles, warnings and normalization results. Storage reduction
is deferred; losing upstream context is not an acceptable optimization.

Gold has separate datasets for:

- `gold_research_evidence`: one row per source block with reading order, section
  identity/classification, exact normalized text and checksum. Table blocks remain
  placeholders. This is the input contract for WP3.6, not tokenized research chunks.
- `gold_tables` and `gold_table_text`: structured grids and the existing separate
  financial-table rendering. Cells and supplemental context resolve through Silver.
  Quarantined grids retain their raw cells and failure events in Silver.
- `gold_reported_facts`: supported USD metric concepts and forms, retaining all
  source occurrences and reporting versions. These are reported observations,
  not a selection for an implicit period or cutoff.
- `gold_metric_definitions` and `gold_selections`: the seven exact WP3.4 definitions
  and results for explicitly supplied requests. Results retain candidates, reasons,
  alternatives, policy, cutoff and source-linked selected observations. Unsupported,
  unavailable and ambiguous requests remain rows, with no invented selected amount.
- `gold_citations`: deterministic references from evidence/table/fact records to
  their Silver source entity, original source identity and DOM/JSON locator.

Unknown or ambiguous sections remain in Gold. Tables never supply or overwrite
XBRL metric facts. Publication is **warning** quality: source preservation and
contract checks do not prove independent financial accuracy. WP33-REV-001 through
-006, JPMorgan quarterly classification gaps, unknown Company Facts dimensions,
narrow metric definitions, and deferred human adjudication remain in every snapshot.

## Physical encoding

`adapters/storage/parquet.py` compiles explicit Arrow schemas from record serialization
schemas, never from samples. Strings and exact decimals use UTF-8; dates use date32;
canonical timestamps use UTC microseconds; embedded Phase 2 timestamps retain their
original offset strings. Integers use checked int64, booleans use bool, nested
models use structs, and tuples use typed lists. Empty lists differ from null.
Schema metadata records contract, encoding, model and schema hash.

PyArrow **24.0.0** is pinned and hash-locked. Output uses fixed row ordering,
4096-row groups, Zstandard level 3, Parquet 2.6, and no dictionary encoding.
Every object is checksum-verified and losslessly revalidated after writing.
Bitwise reproducibility is scoped to the pinned processing/Arrow environment.
Paths and fetch locations do not affect canonical source identities; provenance
rows intentionally record the pinned input fetch metadata.

The build specification pins code revision plus a checksum of installed package
sources, lockfile hash, component versions, requests, and a logical run clock.
The working-tree checksum distinguishes uncommitted builds from the base revision.
Reuse the same specification and inventory for replay. `validated_at` is the pinned
logical run clock, not an elapsed-time measurement; PostgreSQL activation events
record actual wall-clock time. New input, configuration or versions produce a new
dataset version. Do not edit an existing spec to claim an identical run.

## Build and verify

Use a derived root separate from the immutable Bronze root. The supplied request
fixture reproduces WP3.4's 35 annual selection probes; it is an automated regression
input, not independently adjudicated financial ground truth.

```bash
bash scripts/uv.sh run --frozen python -m sec_research.processing.dataset_cli prepare \
  --code-revision "$(git rev-parse HEAD)+working-tree" \
  --run-at 2026-10-22T08:00:00Z \
  --requests tests/fixtures/datasets/requests.json --spec .runtime/wp35/spec.json
bash scripts/uv.sh run --frozen python -m sec_research.processing.dataset_cli build \
  --spec .runtime/wp35/spec.json --dataset-root .runtime/wp35/datasets
bash scripts/uv.sh run --frozen python -m sec_research.processing.dataset_cli verify \
  --dataset-root .runtime/wp35/datasets --snapshot-id 'snapshot:<returned-hash>'
```

Choose and retain an appropriate run clock for a new build. `prepare` uses
create-only output; repeat `build`, not `prepare`, for the same pinned run.
The CLI audits all inventory manifests/objects before and after processing. Both
layers are validated before the final snapshot manifest is written. Missing source
references, orphaned records, mismatched projections, unsupported physical types,
invalid financial periods, inconsistent versions or checksums fail the build.
Unsupported financial units and rejected observations remain explicit Silver
quality records; valid quarantine does not erase the remainder of a source.

## Activation, recovery and rollback

Migration `0003_datasets` adds snapshot catalogs, a singleton active pointer,
snapshot-keyed JSONB serving projections and activation history. Existing Bronze
tables are untouched. Apply migrations explicitly using the development guide.
With `DATABASE_URL` set to the intended local catalog:

```bash
bash scripts/uv.sh run --frozen python -m sec_research.processing.dataset_cli activate \
  --dataset-root .runtime/wp35/datasets --snapshot-id 'snapshot:<new-hash>' \
  --expected-active none
```

For subsequent activation, supply the previously observed active snapshot ID.
The adapter verifies files/manifests and regenerates Gold checks, then locks the
active pointer and compares it with `expected_active`. A single transaction
registers the snapshot, rebuilds its serving projections, updates the pointer,
and records an activation event. Readers pin a snapshot ID and filter projections
by that ID; existing versions remain accessible. No research API is added.

Rollback uses the same command with an older valid snapshot and the current
expected ID. Same-version activation rebuilds projections without adding a
spurious activation event. Transaction failure rolls back all catalog/projection
changes. Stale activation fails explicitly. Artifact or manifest corruption blocks
activation, including rollback. External filesystem mutation after validation is
outside the trusted local immutable-store guarantee; readers should verify files.

Interrupted builds may leave unreferenced content-addressed objects and temporary
files, but no completed snapshot or active pointer. Retry from the same inputs;
existing identical objects are reused, conflicts fail. PostgreSQL failure may leave
a complete inactive filesystem snapshot, which can be activated on retry. No
automatic garbage collection or destructive cleanup is implemented. Catalog
rollback and migration downgrade are different operations: downgrade removes the
derived catalog/projections, while immutable files remain available for rebuilding.

The implementation is bounded by individual source documents and batch writes,
not an established large-corpus memory/runtime SLO. XBRL selection currently reads
source fact partitions per requested company. Envelope redundancy and repeated
integrity validation trade runtime for explicit checks. Review measured corpus
results in [the completion report](phase-3-wp3.5-review.md) before expanding scope.
