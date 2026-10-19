# ADR-001 — Modular application with explicit boundaries

Status: Proposed. Architecture: 3.1. Implementation phase: 1.

## Context

The platform combines ingestion, data processing, retrieval, deterministic finance, research orchestration, and APIs. A portfolio-scale team needs independently testable components without the operations burden of distributed services.

## Decision

Use one `src/sec_research` Python package. Domain types/policies have no framework dependencies. Application use cases depend on narrow ports; SEC, PostgreSQL, object storage, and model adapters implement those ports. API routes, jobs, and graph nodes coordinate use cases. A separate `web/` Next.js application consumes versioned REST contracts.

Deploy API and worker processes from the same versioned package/image as needed. They share contracts and PostgreSQL but have explicit transaction and resource boundaries. Define interfaces before major implementations; do not introduce an abstraction for every function.

## Alternatives and consequences

Flat scripts speed an initial demo but make business rules, test fixtures, and provenance hard to reuse. Microservices offer independent deployment but add network contracts, consistency failures, and operational cost before there is a measured need. A modular application keeps iteration simple while still requiring discipline to prevent cross-module shortcuts.

The frontend has its own build toolchain. Avoid duplicating authoritative financial logic in TypeScript; use generated/validated API contracts where useful.

## Validation and reconsideration

Phase 1 verifies package installation and imports, no network side effects, typed boundary tests, and API/worker entry-point configuration. Revisit a service split only for measured scaling, isolation, release, or ownership requirements. Record its transaction and failure model before separating deployment units.
