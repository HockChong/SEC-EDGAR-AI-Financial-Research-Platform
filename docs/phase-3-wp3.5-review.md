# WP3.5 completion review

2026-10-22, Asia/Kuala_Lumpur. Architecture 3.1 / ADR-003. The initial checkout was
clean `main` at `0635ed4`, containing reviewed WP3.4 commit `20a03bd`. Implementation
remains uncommitted on the existing branch. WP3.6 has not started.

Corpus verification is in progress; final counts and replay evidence will be
recorded here before the package is reported complete.

## Implementation

- `contracts/datasets.py`, `processing/dataset_rows.py` and `processing/datasets.py`:
  versioned Silver/Gold contracts, deterministic projections, source coverage,
  graph/version checks, exact-period selection evidence and immutable paired manifests.
- `adapters/storage/parquet.py`: explicit Arrow schemas, exact decimal strings,
  checked integer/date/timestamp encoding, deterministic Parquet and create-only
  objects, with checksum and lossless round-trip validation.
- `adapters/postgres/datasets.py`, migration `0003_datasets`, and readiness head:
  transactional catalog, snapshot-keyed serving projections, compare-and-swap
  activation, failure rollback and verified reactivation of earlier snapshots.
- `processing/dataset_cli.py`: prepare/build/verify/activate commands. No research
  API, chunker, embedding, financial calculation, or AI framework was added.
- Tests, 35 pinned metric requests, wheel smoke, package guides and status/ADR
  documentation were updated. The owner's concurrent AGENTS efficiency additions
  were preserved.

ADR-003's existing Arrow/Parquet plus PostgreSQL architecture was implemented;
PyArrow 24.0.0 is the only added dependency. Canonical contracts and frozen
WP3.2–WP3.4 processors are unchanged. Supplemental envelopes intentionally duplicate
some canonical cells/facts to preserve and cross-check upstream context. No Spark,
Delta, new storage service or orchestration system is justified by this corpus.

## Verification executed

- Baseline: 404 offline tests passed, ten database tests deselected; lock,
  lint/format and strict typing passed. Initial attempts encountered sandbox
  package-download restrictions and pytest cache permissions; the installed
  environment and disabled cache resolved that baseline.
- Focused Windows development runs: 34 dataset tests passed; the PostgreSQL
  transaction/failure/rollback test passed against a disposable database.
- Final Linux `bash scripts/check.sh`: lock check (45 packages), lint/format
  (100 files), strict typing (94 source files), **462 tests passed**, zero failed,
  skipped or xfailed; branch-aware total coverage **90%**. All eleven PostgreSQL
  tests ran through the dedicated `_test` connection and uniquely named databases.
- Linux `bash scripts/verify-wheel.sh`: wheel/sdist built; 25 hash-locked runtime
  dependencies installed in a fresh environment; API/contracts/CLI smoke and
  deterministic Silver/Gold Parquet replay passed outside the checkout. Container
  exit code was independently verified as zero.

Windows later blocked mypy/SQLAlchemy extension modules through application
control, including a clean wheel environment. No OS protection was changed.
Verification used the repository's pinned Linux Docker builder and a read-only
checkout mount. Shell line endings were normalized only in that temporary copy.
Windows distribution validation remains blocked; Linux validation passed.

The first full Linux run had one failure and 460 passes: the WP3.2 freeze also
pinned the entire old lockfile. The corrected guard removes exactly the authorized
Arrow package and its two dependency entries, then requires the original lockfile
SHA-256. All pre-existing packages, artifact hashes, parser files and labels remain
frozen. The original freeze record was not rewritten, and no assertion was disabled.

## Publication and limitations

Objects and manifests are immutable. Only a fully validated Silver/Gold pair gains
a snapshot completion marker. PostgreSQL activation registers the snapshot,
rebuilds all Gold projections and changes the active pointer in one transaction;
an injected failure leaves the old snapshot visible. A stale expected pointer
fails explicitly. Same-version activation rebuilds projections without another
activation event. Rollback uses the same verified activation path. Partial objects
remain inactive and reusable; automatic garbage collection is not implemented.

Gold keeps narrative/table evidence separate from reported metric observations
and explicit selection results. Unknown/ambiguous sections and rejected source
occurrences survive. Warning-quality publication does not establish financial
accuracy: WP33-REV-001 through -006, JPMorgan quarterly section gaps, unknown
Company Facts dimensions, narrow metric coverage and independent human
adjudication remain unresolved. Automated checks are not independent human
accuracy verification.

The pipeline validates one source partition at a time, but retains redundant
envelopes and performs repeated integrity checks. Large-corpus memory/runtime
targets remain unestablished. Windows and Linux have different bundled libxml
versions, recorded in parser identity; incompatible snapshots are rejected rather
than silently mixed. PostgreSQL publication failure/recovery evidence uses the
synthetic integration corpus; real-corpus activation is not claimed.

Gold block/table evidence contracts are ready for a separately authorized WP3.6
chunker. The next step is WP3.5 acceptance review, followed by WP3.6 only with
explicit authorization. No commit or push was performed.
