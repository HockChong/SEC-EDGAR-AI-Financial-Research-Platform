# ADR-010 — Bronze coordination and immutable publication

Status: Accepted for Phase 2 implementation. Architecture: 3.1.

## Context and decision

ADR-003 requires auditability across filesystem publication and PostgreSQL state.
The existing foundation already supplies PostgreSQL, typed settings and local storage
configuration. A new broker, database or distributed storage service has no workload
justification in this phase.

Use a shared PostgreSQL rate clock, transaction advisory lock and database time to
coordinate request starts across CLI processes. Session advisory locks claim individual
source URLs across intermediate work commits; connection loss releases claims without
a separate lease daemon. The source lock reserves one pool connection; ingestion
therefore requires a pool of at least two. One shared database defines the coordination
boundary. Embedded single-process clients can use a shared local limiter.

Publish complete checksum-addressed local objects and JSON fetch manifests with atomic
create-only hard links. Never use replace/overwrite for Bronze. Verify existing bytes,
then append PostgreSQL fetch history and finish operational work in one transaction.
Triggers prevent update/delete of fetch and attempt history. Invalid complete payloads
retain a quarantined version; unknown source fields remain in raw bytes. Failed work
retains a safe error code and actual HTTP-attempt count rather than exception text.

Default immutable filing reuse and 24-hour mutable-JSON reuse are explicit fetch
policies. Refresh uses conditional validators, appending a fetch observation even for
304 while sharing the immutable object. This preserves source and document identity
independently of byte identity. Schema `1` and pipeline `bronze-1` identify the contract.

## Alternatives and consequences

Filesystem-only manifests lack shared request coordination and transactional work
history. SQLite would duplicate the existing PostgreSQL responsibility. A per-process
rate limit multiplies across workers. Object overwrite or unconditional rename can
destroy the authoritative source. Distributed transactions and object-store adapters
would add unneeded infrastructure; the typed storage boundary permits later adapters.

Atomic hard links require a suitable local filesystem. Administrator writes can still
alter bytes, so verification detects corruption rather than claiming WORM guarantees.
The object/SQL boundary can leave orphan objects/manifests, handled by restart and
read-only reconciliation. Abandoned staging files and orphan manifest cleanup are
documented debt. A killed run remains historically running until an explicit operator
decision; recovery creates a new run instead of fabricating completion.

Nonempty ingestion downgrades refuse to erase source history. Operational rollback
therefore requires backup and a deliberate data migration. Retained source history is
more valuable than an automatic destructive rollback. Silver/Gold publication,
financial interpretation, object-store conditional creation and large-corpus processing
remain later work under ADR-003.

## Validation and reconsideration

Unit and real PostgreSQL tests cover retries, fair-access budgets, URL boundaries,
malformed envelopes, immutable writes, duplicate/mutable versions, source claims,
durable start/failure/completion, interruption/recovery, checksums, and migration refusal.
The CLI is exercised with mocked SEC transport and real temporary databases. After mocked implementation verification, a user-executed one-company live
SEC ingestion/reuse/integrity check passed; see the Phase 2 review. Reconsider storage/coordination
only with a multi-host storage requirement or measured workload evidence.
