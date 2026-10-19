# Testing strategy

Status: requirements for future implementation. Phase 0 has no application tests or runtime checks; documentation verification is recorded in the phase review.

## Test layers

| Layer | Scope | Examples and dependencies |
| --- | --- | --- |
| Unit | Deterministic logic without network/database/model | Period validation, decimal math, concept eligibility, chunk boundaries, retry policy, state transitions |
| Contract | External payload and internal interface compatibility | SEC JSON/HTML fixtures, Pydantic tool/report schemas, OpenAPI snapshot, provider adapter responses |
| Integration | Actual dependencies and transaction semantics | PostgreSQL/pgvector, Alembic migrations, full-text/vector filters, artifact store, checkpoint/job recovery |
| End-to-end | User-visible research path | Request → evidence/facts → calculations → validated report → source inspection; deterministic model adapter by default |
| Evaluation | Quality and performance on versioned datasets | Retrieval ranking, answer support, finance accuracy, task success, cost/latency; see evaluation strategy |
| Operational/security | Failure, isolation, and deployment behavior | Authorization, prompt injection, resource limits, cancellation, backup restore, load and rollback |

Do not use an SQLite substitute to declare PostgreSQL/pgvector integration passed. A fake model tests application behavior but cannot establish real model quality. Deterministic end-to-end and opt-in live-provider tests must be labeled separately.

## Fixtures and isolation

Commit small reviewed fixtures with source URLs/accessions, fetch provenance, checksums, licensing/source notes, and expected outcomes. Include permitted SEC excerpts for happy paths and synthetic fixtures for malformed/adversarial cases. Never commit large downloaded corpora or credentials. Synthetic financial values must be clearly labeled and cannot appear as real-company benchmark findings.

Default unit/contract CI runs offline. Inject clocks, randomness, HTTP transports, provider adapters, and storage interfaces. Integration tests use a real isolated PostgreSQL database with rollback or per-test/schema cleanup; never point destructive tests at a user database. Use dedicated temporary artifact directories. Contract fixtures cannot load external HTML/XML resources.

## Required scenarios by phase

- **1:** clean locked install; package import; configuration validation and secret-safe errors; database ready/migration up and supported rollback path; logging redaction; API health behavior where introduced; nonzero baseline tests and container build checks.
- **2:** correct SEC identification; global rate limiting; Retry-After and jitter/deadline behavior with injected clock; 403/429/5xx policy; malformed/oversize responses; old submissions pagination; amendments; partial downloads; checksum verification; same-run/repeated-run idempotency; changed endpoint response preserving prior artifact.
- **3:** malformed and diverse 10-K/10-Q HTML; duplicate headings; table-of-contents confusion; multi-level table headers and footnotes; negative/parenthesized numbers; unknown scale; Company Facts duplicates; actual dates versus `fy`/`fp`; leap/52/53-week years; instant versus duration; unknown dimensions; conflicting values; later reports; deterministic replay and publication rollback.
- **4:** dense/keyword retrieval against labeled cases; company/date/form/as-of filters including adversarial negatives; empty results; index/model dimension mismatch; approximate-search under-return; parent expansion filter preservation; citation resolution and unsupported-claim handling; API contract and representative research request.
- **5:** tool argument validation and authorization; deterministic formulas, zero/nonpositive denominator policies, percentage points; historical selection; Q4 derivation constraints; bounded retries/repair; budget consumption; provider timeout; worker termination and restart; checkpoint compatibility; cancellation; job lease races; repeated idempotency key with changed payload; UI progress and source inspection.
- **6:** metric computations against hand-calculated examples; split/annotation integrity; baseline reproduction; judge calibration; injection evaluation; cost/token accounting; regression report provenance.
- **7:** user/tenant isolation; secret rotation and redaction; input/rate/usage limits; restore drill; migration/rollback; load test at a declared workload; failed deployment and alert behavior.
- **8:** documented fresh setup; demo flow; accessible report/citation/calculation UI; links; reproducibility of displayed evaluation results and portfolio claims.

Use parameterized and property-based tests where they check real invariants: reordering candidates cannot change selection; incompatible units are rejected; repeated ingestion cannot change immutable bytes; adding future filings cannot affect an earlier as-of result; equivalent deterministic runs produce the same calculation records. Avoid tests that merely duplicate an implementation's internal steps.

## CI and developer commands

Phase 1 will define executable commands and scripts after dependency/tool versions are pinned. Intended checks are frozen environment sync, Ruff, mypy, pytest unit/contract, PostgreSQL integration, package build, and container build. These are planned checks, not commands verified in Phase 0. Frontend lint/type/test/build checks begin when `web/` exists.

Keep fast deterministic checks mandatory on PRs. Run database tests on an isolated CI service. Live SEC/model checks are explicitly marked and gated by access, fair-use limits, and budget; they must not silently make offline CI flaky. Provider outage cannot be reported as an application assertion passing. Trusted scheduled evaluation may run separately from PR checks.

Every test runner invocation must preserve its exit status. Record collected/executed counts and passed, failed, skipped, expected-failure outcomes. A zero-test run is not validation. Check that report files belong to the current run; never reuse a stale success artifact.

## Acceptance and reporting

Financial selection, authorization, provenance, and idempotency behavior require explicit edge-case coverage regardless of global line coverage. Track branch/line coverage as diagnostics; adopt a coverage threshold only after meaningful tests exist. No overall percentage can excuse an untested critical invariant.

Package reviews record commands, environment/dependency versions, counts, failures and diagnoses, skipped/unrun checks and reasons, and remaining limitations. Required unexplained failures block that package's acceptance. Confirmed repository defects must be reported with evidence; do not disable tests or invent results to clear a gate.
