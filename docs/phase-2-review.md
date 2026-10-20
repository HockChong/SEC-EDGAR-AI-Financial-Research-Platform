# Phase 2 acquisition review

Review date: 2026-10-20. Architecture: 3.1. Scope: independently verify Phase 1,
then implement the explicitly authorized Phase 2 only. Work remains in the existing
checkout on `main`; no worktree, commit, push, publication or Phase 3 work was performed.

**Outcome:** Phase 2 is complete for the bounded acceptance scope. Automated checks
passed, and the user subsequently completed live SEC ingestion, repeated ingestion
without new downloads, and integrity reconciliation. The original mocked-only choice
applied to the implementation gate; the live evidence below closes its outstanding
smoke check. This does not establish broad corpus coverage or production readiness.

## Initial audit and Phase 1 gate

Inspected AGENTS, requirements, roadmap, architecture/data/security/deployment guidance,
ADR-003, data dictionary, testing/evaluation strategies, Python package/configuration,
API, PostgreSQL adapter/migrations, Docker/Compose, CI, scripts, tests and Git status.
There was no partial Phase 2 implementation to duplicate. The existing changes in
`docs/development.md` and `scripts/verify-wheel.sh` added Windows wheel-path support;
they were preserved and the latter was extended to verify the installed ingestion CLI.

Independently reproduced the foundation gate before implementing ingestion:

- Git Bash `scripts/check.sh` with the dedicated `sec_research_test` connection:
  lock consistency, lint/format and strict typing passed; **33 tests passed**, zero
  failed/skipped/expected failures, **97% coverage**.
- Git Bash `scripts/verify-wheel.sh`: wheel/sdist build, hash-checked dependency
  installation, typed marker, API import and schema verification passed outside the checkout.
- Elevated `docker version`, `docker compose ps --all` and a read-only catalog query
  verified the healthy existing PostgreSQL/pgvector service and dedicated test database.
  Current Docker client/server are 29.9.1; Python is 3.12.14 and uv is 0.12.23.
- Reviewed historical Phase 1 evidence separately. Hosted CI, container rebuild/start
  and cloud-environment restoration were not independently rerun or claimed here.

No blocking Phase 1 defect remained. Database tests continued to create/drop uniquely
named databases through the dedicated `_test` connection; the development database
was not migrated by those tests.

## Work packages and contracts

The bounded implementation plan was transport/contracts, discovery/immutable storage,
then Company Facts/replay/CLI, following roadmap packages 2A–2C. The requested WP2.1–2.6
features are covered within those packages. No new dependency, infrastructure service,
agent, parsing framework or AI integration was introduced; `pyproject.toml` and `uv.lock`
are unchanged.

### 2A / WP2.1: SEC transport and contracts

Created `contracts/sec.py`, `adapters/sec/{__init__,client}.py` and synthetic transport
tests. Defined canonical ten-digit CIKs, dashed accessions, filing/document/source
identity, typed failures and bounded transport policy before persistence components.
The reusable client supports submissions, Company Facts, historical submissions,
official ticker lookup and filing archive paths through its allowlisted GET interface.

Implemented real identifying User-Agent validation, verified HTTPS, no redirects or
ambient proxies, original-byte responses, time/size/attempt bounds, aggregate limits,
retryable HTTP/network handling, exponential jitter, Retry-After and safe event logging.
Current official SEC guidance was checked: aggregate ceiling ten requests/second;
the application caps starts at five. Sources are linked in the ingestion guide.

Initial package verification: **31 transport/identifier tests passed** and strict
typing passed. Initial lint line-length findings were formatted/fixed, not suppressed.
The final suite additionally tests the actual HTTPS adapter with mocked connections,
including TLS context, truncation, oversized bodies, redirects and connect-time budgets.

### 2B / WP2.2–2.4: Discovery, Bronze and manifests

Created company/filing discovery, envelope validation, typed storage/manifest ports,
local immutable storage, PostgreSQL manifest/rate coordination and `0002_ingestion`.
Updated API readiness to the new migration head. Discovery traverses every overlapping
referenced history file, applies inclusive filing-date/form filters, preserves optional
report/acceptance metadata, and detects duplicate conflicts. Amendments are explicit.

Original JSON/HTML bytes are staged, fsynced and published create-only under SHA-256;
manifest JSON is also immutable. PostgreSQL separates mutable work state from append-only
fetch/attempt history. Source metadata records company, filing accession/form/date,
document name/URL, storage URI, checksum, acquisition timestamp, status and attempts.
Malformed complete payloads retain quarantined bytes; transport truncations cannot
become successes. Every successful cache read verifies integrity.

Package verification progressed to **83 offline tests passed, 10 integration tests
deselected**, with lint and strict typing passing. A real PostgreSQL run then passed
**10 integration tests**, covering the five existing foundation cases plus persistent
manifests, immutable history, source claim exclusion, aggregate rate timing,
interrupted work/failure/resume and mocked CLI execution. The later final suite includes
additional failure paths and migration protection.

### 2C / WP2.5–2.6: Company Facts, replay, CLI and verification

Created Company Facts acquisition, freshness/conditional refresh, recoverable orchestration,
the module CLI and read-only reconciliation. Changed JSON responses append versions;
identical bytes deduplicate without collapsing fetch/document identity. Filing bytes
are reused indefinitely unless explicitly refreshed; mutable JSON defaults to 24 hours.
304 requires verified prior bytes. Ordinary partial failures allow independent work
to complete; access denial/rate exhaustion/deadlines stop the run.

Tests demonstrate restart after publication but before SQL completion, missing-work-only
retries, repeated CLI ingestion without new HTTP downloads, checksum and manifest
tampering detection, invalid configuration/metadata, history traversal, Company Facts
versions and original lexical decimals, and disk-full publication failure. The synthetic
corpus and its checksum inventory are in `tests/fixtures/sec/`; they are not live SEC data.

Created `docs/ingestion.md`, this review and ADR-010; updated status/configuration guidance
in README, AGENTS, architecture, dictionary, roadmap, testing/development docs, ADR-003
and ADR index. `.env.example` has an intentionally empty SEC identity and bounded
transport defaults; no private credential or invented live contact is included.
Added `.gitattributes` to preserve exact fixture bytes across checkout newline settings,
plus a five-fixture checksum/source inventory under `tests/fixtures/sec/manifest.json`.

## Architecture decisions and deviations

- Reused the existing PostgreSQL infrastructure and standard-library HTTPS transport.
  No dependency or lockfile churn. Domain/discovery logic has no FastAPI or AI dependency;
  persistence/storage sit behind typed ports.
- Accepted the Bronze portion of ADR-003 and documented its implementation in ADR-010.
  Silver/Gold, financial normalization and dataset publication remain proposed.
- A database-wide rate clock and advisory lock coordinate CLI processes. Source session
  locks release on connection loss and avoid a lease scheduler. At least two pool
  connections are required for ingestion; defaults provide five. All CLI processes
  must share one coordinating database and artifact root.
- Atomic hard links provide create-only local publication. Replace/overwrite, a second
  database, message broker, distributed transaction and object-store adapter were rejected
  as unnecessary for this phase. Suitable local filesystem support is required.
- Nonempty ingestion downgrade is refused to avoid erasing provenance. Empty schema
  downgrade/reapply preserves existing foundation vector data and is covered by tests.
- Initial implementation verification was mocked-only at the user's request. The user
  subsequently executed the bounded live smoke commands recorded below. The agent did
  not make additional SEC requests; independent follow-up read only local source bytes.

## Commands and measured results

Commands ran from the checkout in Git Bash, invoked through its full executable path
on Windows. The full suite used only the dedicated `_test` connection as the admin
entry point; fixtures created and dropped their own isolated databases.

- `bash scripts/check.sh` with `TEST_DATABASE_URL` set: **passed**. Final run:
  locked 42-package resolution, Ruff lint, format (**44 files**), strict mypy
  (**43 source files**), **108 tests passed**, **0 failed, 0 skipped, 0 xfailed**,
  **92% total branch-aware coverage**, **12.16 seconds** test time. Composition:
  **92 unit, 6 API contract, 10 PostgreSQL integration tests**.
- `bash scripts/verify-wheel.sh`: **passed** after the final code change. Built wheel
  and sdist, installed 23 hash-checked locked runtime dependencies into a clean temporary
  environment, installed the wheel, and verified `py.typed`, API schema and ingestion
  CLI `--help` from outside the source checkout.
- Targeted `uv run --frozen pytest tests/unit/test_sec_client.py`: **31 passed** at the
  first package gate. Subsequent offline package runs passed 83 and then 97 cases with
  ten integration cases deselected; the final full run above supersedes those counts.
- `uv run --frozen pytest tests/integration --cov=sec_research --cov-report=term-missing`:
  **10 passed** at the first integration gate. Its 74% whole-package coverage reflects
  an integration-only selection, not the final full-suite result.
- `uv run --frozen ruff check src tests migrations`, `ruff format`, and `mypy`:
  passed during incremental gates and as part of the final check script.
- `uv run --frozen python -m sec_research.ingestion.cli --help` and `... ingest --help`:
  **passed**. The real CLI entry function also ran twice against temporary PostgreSQL
  with mocked SEC responses; the second run made zero additional HTTP calls. Reconcile
  verified five fetch records backed by four unique objects and zero orphan objects.
- `bash -n scripts/verify-wheel.sh`, `git diff --check`, local documentation-link,
  distribution-content and fixture-inventory checks are recorded in the final audit below.

Coverage is diagnostic; it is not a benchmark or a claim of universal correctness.
No previously unexecuted check is reported as passing.

## Diagnosed errors

Initial sandbox checks encountered a protected existing pytest cache and denied package
registry/Docker access. Required checks succeeded with the necessary execution access;
tests/assertions, TLS and artifact hash verification were not weakened. Intermediate
offline runs also used a separate writable pytest cache.

Early tests exposed test-helper package discovery and duplicate test basenames. Added
the test package marker/shared helpers and gave the PostgreSQL test module a unique name.
One discovery test initially attempted historical access before rejecting unsafe recent
metadata. Moved complete envelope/filing metadata validation before downstream access;
the source is now preserved and quarantined immediately. Type/lint failures were fixed.
There are no unexplained failures in the final run.

## Acceptance, limitations and next gate

Satisfied with deterministic evidence: reusable bounded SEC client; exact company/CIK
lookup; recent/historical filing discovery; 10-K/Q and opt-in amendment acquisition;
original-byte immutable Bronze; Company Facts preservation; persistent manifest and
status/retry/error history; idempotency; safe partial-failure recovery; checksums;
documented CLI; passing automated tests, lint/type and distribution checks.

The outstanding bounded live check is now satisfied by user-executed commands and
independent local byte verification, recorded below. The user's setup reported a healthy
database and ready schema. Keep the artifact root stable for reuse. No contact address
or private environment value is copied into this review.

Known limits and debt:

- Local trusted storage with hard-link support; not WORM, object-store durability or
  backup verification. Coordinating databases cannot govern unrelated SEC traffic.
- Reconciliation checks committed manifests/objects and reports orphan object counts;
  it does not delete objects, import orphan manifests, clean staging files or repair
  corruption. Orphan manifest/staging retention and streaming large-corpus scans are debt.
- Killed runs can remain historically `running`; subsequent run IDs record recovery.
  A source session lock is released on connection loss. No background scheduler exists.
- Default JSON freshness can reuse a previous valid response for 24 hours. Use refresh
  when a new observation is needed. Reused cache reads do not create new fetch observations.
- Company Facts validates identity/envelope only; concept/context/financial validation
  belongs to Phase 3. No observation periods are inferred from `fy`.
- Filing primary documents must be simple HTML filenames; unsupported text-only or
  unusual legacy primary documents fail explicitly. HTML semantic validation is deferred.
- Hosted CI, new container builds/start, cloud restoration, production deployment,
  financial performance and throughput benchmarks were not run. Live network evidence
  is limited to the user-executed one-company smoke check below.

Recommended next package: separately authorized **Phase 3A document parsing**, with
additional corpus coverage chosen explicitly within that assignment.
No Phase 3 work is started. Stop at this Phase 2 review gate.

## Final audit

The final review preserves the preexisting Windows changes, keeps dependency/lockfiles
unchanged, and excludes runtime databases, downloaded corpora, distributions and caches
from versioned source. `git diff --check` and `bash -n scripts/verify-wheel.sh` passed.
A Python local-link/fence check passed for **30 Markdown documents and 92 local links**.
The five synthetic fixture byte counts and SHA-256 values match their committed inventory.
Git emits a nonblocking sandbox warning when reading the user's protected global ignore;
repository status/diff checks still complete. No source was staged, committed or pushed.
Distribution inspection passed: **30 wheel entries** include the CLI and typing marker;
**100 sdist entries** include this review and fixture inventory, with no private `.env`,
cache, virtual-environment or runtime tree. The final documentation update was included
by an offline rebuild using the same pinned backend. No dependency/lockfile changes remain.

## Live acceptance closure: 2026-10-20

Evidence sources: terminal output supplied by the user, plus an agent read-only check
of the three local Bronze manifests and object byte counts/SHA-256 values. The agent
made no additional network requests or development-database changes for this closure.
The compact [live corpus inventory](phase-2-live-smoke.json) records source URLs,
accession, fetch IDs, checksums and sizes; raw source bodies remain outside Git.

The user ran `scripts/setup.sh`; its output reported the database healthy and the
foundation dependencies, PostgreSQL and schema ready. In PowerShell, the user then ran:

```powershell
& $gitBash scripts/uv.sh run --frozen python -m sec_research.ingestion.cli ingest --company 0000320193 --from-date 2025-01-01 --max-filings 1
& $gitBash scripts/uv.sh run --frozen python -m sec_research.ingestion.cli reconcile
```

First ingestion: three HTTP 200 response events and three acquisition-success events.
Run `3430fe5e-19f3-4ff3-91b1-b29067f6a41f` returned one company, one filing, one Company
Facts acquisition and an empty error list. First reconciliation reported three fetches,
three objects and zero orphans.

The user repeated the exact ingestion and reconciliation commands. Run
`e86ef8fb-d64f-4459-a8d4-84208dc57d92` returned the same successful counts and an empty
error list with no new SEC response/acquisition events. Second reconciliation again
reported three fetches, three objects and zero orphans. This demonstrates cache reuse
without duplicate fetch records or objects for this corpus.

Independent local verification matched all three stored SHA-256 values and byte counts:
submissions JSON (163778 bytes), Company Facts JSON (3789099 bytes), and primary filing
HTML (1018316 bytes). The filing metadata identifies Apple CIK `0000320193`, form `10-Q`,
accession `0000320193-26-000020`, filing date `2026-07-31`, report date `2026-06-27`, and
primary document `aapl-20260627.htm`. These are recorded source metadata, not new
financial interpretations.

This live check covers one company and one quarterly filing; historical submissions
traversal, 10-Ks, amendments, failures and crash recovery remain supported by deterministic
tests rather than claimed as live-tested here. No refresh/304 or multi-company live
benchmark is claimed. Earlier automated results remain 108 passed with 92% coverage;
those checks were not rerun for this documentation-only closure. Architecture and
runtime behavior did not change. Phase 3 remains unstarted.

Closure checks passed: 30 Markdown documents, 93 local links, balanced code fences,
live-inventory schema/count sanity, and `git diff --check`. No runtime code, dependency,
lockfile, private contact setting or downloaded source body changed in this closure.
Distribution artifacts were not rebuilt for these documentation-only updates.

## Independent re-verification: 2026-10-20

At the user's request, rechecked the current implementation against Phase 2 packages,
contracts, architecture and acceptance criteria. No blocking Phase 2 defect was found.
No runtime code, architecture decision or dependency changed; this review is the only
source document updated by the re-verification.

Commands actually rerun and their outcomes:

- `bash scripts/check.sh` with the dedicated `sec_research_test` connection: passed.
  Lock validation, Ruff lint, format (44 files), strict mypy (43 source files), and
  **108 tests passed in 17.27 seconds**, with **0 failures/skips/expected failures**
  and **92% branch-aware coverage**. Tests used uniquely named temporary databases.
- `bash scripts/verify-wheel.sh`: passed. Rebuilt wheel/sdist, installed hash-verified
  locked dependencies in a clean temporary environment and checked the installed
  typing marker, health-only API schema and ingestion CLI outside the checkout.
- `python -m sec_research.ingestion.cli reconcile` through the locked runner against
  the existing development database: passed, reporting **3 fetches, 3 objects,
  0 orphans**. This was read-only and made no new SEC requests.
- Independently verified the recorded SHA-256 and byte count of all **3 live objects**
  and **5 synthetic fixtures** against their inventories: passed.
- Documentation links/fences: **30 Markdown documents and 93 local links passed**.
  `git diff --check` and shell syntax validation passed. Dependency and lockfiles have
  no diff. Git ignore checks confirmed raw artifacts and preview copies are excluded.
- Distribution inventory: **30 wheel entries** include the CLI and typing marker;
  **101 sdist entries** include the live inventory and exclude private environment,
  runtime, cache and virtual-environment trees. These artifacts were built before
  recording this re-verification addendum; application code is unchanged.

The user-executed live ingestion/reuse evidence above remains valid; current database
reconciliation independently corroborates the persisted corpus. Its live scope is one
Apple quarterly filing plus submissions and Company Facts. Other filing forms/history,
transient failures and interruption recovery are covered by deterministic tests. Hosted
CI, deployment, large-corpus throughput and backup recovery remain unrun and are not
claimed by this phase. Existing retention/reconciliation/legacy-document limits remain
documented debt, with no new acceptance blocker.

Verdict: **Phase 2 complete for the agreed bounded acquisition scope**. Changes remain
local and uncommitted; no push or publication was performed. Recommended next package:
**Phase 3A document parsing**, only after explicit authorization. Phase 3 is unstarted.
