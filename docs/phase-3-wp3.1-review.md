# Phase 3 — WP3.1 review

Review date: 2026-10-20. Architecture: 3.1. Authorized scope: **WP3.1 only**.
WP3.2 has not started. Existing Phase 2 work remains local and uncommitted on
`main`; no worktree, branch switch, commit, push or dataset publication was performed.

**Outcome:** WP3.1 canonical contracts, portable storage-row schemas and
representative synthetic fixtures are implemented and verified. This is a
contract gate, not completion of Phase 3 or validation of a parsing/RAG pipeline.

## Repository audit and prerequisites

Read root AGENTS, requirements, architecture/data guidance, the data dictionary,
roadmap, testing/evaluation/development instructions, ADR-003 and ADR-006, and the
Phase 2 review/live inventory. Inspected Phase 2 source/filing/fetch contracts,
acquisition and CLI, Company Facts ingestion, SEC client, immutable local storage,
PostgreSQL manifests, fixture/test conventions and pinned dependencies.

The request named five paths that do not exist in this checkout:

- `docs/PROJECT_SPEC.md`: used `docs/requirements.md`.
- `docs/ARCHITECTURE.md`: used `docs/architecture/system-overview.md` and
  `docs/architecture/data-architecture.md`.
- `docs/DATA_CONTRACTS.md`: used `docs/data-dictionary.md`.
- `docs/EVALUATION.md`: used `docs/evaluation-strategy.md`.
- `docs/adr/ADR-003.md`: used `docs/adr/ADR-003-data-pipeline.md`.

`docs/ROADMAP.md` resolves to existing lowercase `docs/roadmap.md` on Windows.
No contents were invented for absent files. The original attachment ends in
WP3.7 at “Publish a”; the subsequent explicit WP3.1-only instruction fully defines
this package and avoids depending on the missing tail.

The working tree already contained substantial Phase 2 changes. They were
preserved. Initial offline baseline: **98 passed, 10 integration tests deselected**.
Full baseline against dedicated `sec_research_test`: **108 passed**, no failures,
skips or expected failures, **92% branch-aware coverage**, 13.83 seconds.
Lock, lint/format and strict typing also passed.

Company Facts acquisition is implemented and tested: raw response versions,
immutable bytes, decimal-preserving JSON decoding and replay behavior are present.
Financial normalization and metric selection are not Phase 2 capabilities.
No Phase 2 defect blocking WP3.1 was found.

## Changes

Created:

- `src/sec_research/contracts/canonical.py`: 13 versioned Pydantic record families
  plus source, locator, period, dimension, mapping and dataset-object value models.
- `src/sec_research/contracts/bronze.py`: pure Phase 2 fetch/byte validation bridge.
- `src/sec_research/contracts/schemas.py`: serialization schema registry and
  revalidating deterministic storage-row encoder.
- `docs/schemas/canonical-1.json`: generated storage-row schema bundle.
- `tests/contract/test_canonical.py`: **92 new contract tests**.
- `tests/fixtures/canonical/{annual.htm,quarter.htm,malformed.htm,company_facts.json}`:
  four small synthetic source fixtures, with `manifest.json` and `README.md`.
- `docs/canonical-contracts.md` and this package review.

Extended `.gitattributes` for exact-byte fixture portability; appended WP3.1
guidance to ADR-003, data dictionary and roadmap; extended the existing
`scripts/verify-wheel.sh` to verify canonical imports/schema/period round trips
outside the checkout. Existing Phase 1/2 runtime modules were not edited.

## Decisions and limits

The implementation follows ADR-003 and ADR-006 without an architecture change.
It reuses existing Pydantic/stdlib dependencies; `pyproject.toml` and `uv.lock`
have no changes. Parser, Arrow and tokenizer dependencies are not needed at this
contract-only gate.

Portable serialization JSON Schemas define storage rows now. Actual Arrow
allocation, Parquet round trips, manifests written to storage, projections and
publication remain WP3.5–3.7. The precise physical mapping and its lossless
decimal-string requirement are documented in the contract guide. No SQL tables or
second source of truth were created.

Content-derived IDs include schema/pipeline/component versions and source
identity. Financial occurrence rows preserve duplicates and source locations;
a separate logical observation ID supports future deduplication without erasing
reporting history. Publication membership will avoid cyclic snapshot/chunk IDs.
Metric definitions are schemas only; no approved mappings or calculations are
claimed.

Record-local validation cannot establish cross-row referential integrity, source
locator resolution, section accuracy, table-grid integrity, semantic mapping,
actual row counts or atomic publication. Those remain assigned to their later
packages. Contract-valid publication metadata is not proof of actual publication.
Primary documents match Phase 2 coverage; exhibit ingestion requires a future
source-contract extension.

The fixtures are hand-authored and clearly synthetic. They represent important
edge cases, not broad real-filing accuracy or a measured retrieval benchmark.
No real SEC source bodies, private environment values or new credentials were
added to versioned files.

## Commands and actual outcomes

Commands ran through `C:\Program Files\Git\bin\bash.exe`; the `bash` command on
PATH points to a WSL launcher that initially failed with access denied. Python
3.12.14 and uv 0.12.23 use the existing frozen lock.

- `bash scripts/check.sh` baseline and final runs: lock validation, Ruff lint and
  formatting, strict mypy and tests passed. The final run checked 49 formatted
  files and 47 typed source files.
- Final offline suite: **190 passed, 10 deselected**, 2.15 seconds.
- Final full suite with
  `TEST_DATABASE_URL=postgresql+psycopg://sec_research:sec_research_dev@127.0.0.1:5432/sec_research_test`:
  **200 passed**, **0 failed, 0 skipped, 0 expected failures**, 14.92 seconds,
  **93% branch-aware coverage**. The URL uses the repository's public disposable
  development credentials; integration fixtures created/dropped only uniquely
  named databases through the dedicated `_test` connection.
- `bash scripts/verify-wheel.sh`: **passed**. Built wheel/sdist, installed locked
  runtime dependencies with hash verification into a clean temporary environment,
  installed the wheel, and verified canonical contracts, typing marker, health
  API and ingestion CLI outside the checkout.
- `python -m sec_research.ingestion.cli reconcile`, through the locked runner with
  the existing local development database: **3 fetches, 3 objects, 0 orphans**.
  This was read-only, with no new SEC requests.
- Independent local Python integrity/compatibility check: verified all three live
  artifacts against `docs/phase-2-live-smoke.json` and their stored fetch manifests;
  Company Facts **3,789,099 bytes**, submissions **163,778 bytes**, filing
  **1,018,316 bytes**. All SHA-256 and length checks passed. The existing Apple
  filing converted to canonical filing/document contracts without metadata loss.
  No processed artifacts were written.
- Four new fixture hashes/envelopes and all five existing Phase 2 fixture hashes
  were checked by the contract suite.
- Final diff/secret/generated-file review and `git diff --check` passed. Existing
  user changes remain intact; dependency/lock files have no diff. Git ignore checks
  confirmed raw artifacts, previews, test cache and distributions stay excluded.
- Documentation link/fence checks passed for the six changed/new Markdown files;
  the final roadmap status update adds one more valid review link. Bash syntax
  validation of the modified wheel script passed.
- Distribution inventories passed: **33 wheel entries** include the three new
  contract modules; **113 sdist entries** include the schema bundle and all six
  fixture/notes files, excluding runtime, venv and private `.env` files. These
  archives were built before this final review/status documentation was written;
  the verified application and tests are unchanged.

Initial failures were diagnosed rather than hidden:

- The default pytest cache was inaccessible; tests reached completion but shutdown
  failed. Reran using `PYTEST_ADDOPTS='-o cache_dir=.runtime/pytest-phase3'`. This
  changes only cache location, not test selection or assertions.
- First focused contract run: **91 passed, 1 failed** due to an incorrect literal
  golden checksum in the new test. Recomputed the specified literal JSON byte
  vector independently with SHA-256 and corrected the expected value. Initial
  Ruff formatting/style findings and one heterogeneous-list typing error were
  also fixed; none remain.
- Initial wheel verification could not reach PyPI from the network sandbox.
  An approved retry completed with unchanged dependency pins, TLS and hash checks.

Hosted CI, container rebuild/deployment, new live SEC downloads and large-corpus
performance were not run. They are not claimed by this contract gate. Later-phase
parsing, normalization, selection, publication, retrieval and model evaluations
were not run because those capabilities are outside WP3.1.

## Acceptance and next gate

WP3.1 acceptance is satisfied for its bounded scope: all requested record families
have documented/versioned contracts and storage-row schemas; deterministic IDs,
Decimal serialization and uncertainty invariants are tested; representative
fixtures are inventoried; Phase 2 compatibility is verified with both synthetic
and existing live Bronze artifacts; full regression and distribution checks pass.

**Stop for review.** The recommended next package is **WP3.2 — deterministic SEC
HTML parsing and form-aware section extraction**, only after explicit authorization.
No WP3.2 implementation has begun.
