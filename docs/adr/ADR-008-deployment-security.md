# ADR-008 — Local Compose and gated managed deployment

Status: Accepted for local Phase 1 development; Phase 7 cloud/security decisions remain Proposed. Architecture: 3.1. Implementation phases: 1 and 7.

## Context

The project needs a reproducible local workflow before cloud infrastructure. Public SEC sources do not make user research history, provider credentials, or execution tools safe to expose without authorization.

## Decision

Use Docker Compose with PostgreSQL/pgvector and local artifact storage for development. Run API and worker entry points from the same application package. Select a managed container platform, PostgreSQL service, object storage, and secret manager in Phase 7; defer provider/region selection until capability, cost, residency, and restore requirements are known.

Require authentication, per-object authorization, quotas, request/job budgets, secret management, redacted telemetry, restricted network/tool access, and tested backup/restore before shared deployment. Prompts cannot enforce authorization. Ingestion and parser controls apply from their introduction, even during local development.

## Alternatives and consequences

Cloud-only development creates unnecessary cost/access dependencies. Kubernetes, Kafka, extra databases, and independent services add operations without a current need. Local unauthenticated development is simpler but must remain isolated and cannot be used as a shared deployment configuration.

Managed infrastructure reduces operational burden but still requires migration, connection, extension, backup, and recovery testing. Private research data needs retention and deletion policy even when the underlying SEC filings are public. Cloud-environment proxy credentials may not be suitable for local password/encryption-key uses.

## Validation and reconsideration

Phase 1 tests clean setup, database/extension readiness, migrations, and repeatable startup. Phase 7 tests identity/access isolation, secret rotation, TLS/network policy, load, failure recovery, rollback, and actual backup restore. Revisit infrastructure only from measured operating requirements and an updated threat model.

## Phase 1 implementation boundaries

Compose binds the API/database to host loopback; the API image runs as non-root. The local database uses explicitly public development credentials and a role able to create extensions/test databases. Migrations are explicit, and downgrade retains the vector extension/data. App production mode is rejected until shared-deployment controls are implemented. Container builds can mount an approved CA bundle for verified package access without embedding it. These local checks do not establish production readiness.
