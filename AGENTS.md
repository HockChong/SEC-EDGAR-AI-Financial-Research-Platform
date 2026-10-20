# Development instructions

## Scope and authority

- Follow architecture version 3.1 in [requirements](docs/requirements.md) and the architecture documents. Inspect existing code, documentation, tests, configuration, and Git status before editing.
- Implement only the explicitly assigned phase or work package. Do not combine major phases into an uncontrolled change. Stop at the end of every assigned package, report the results, and wait for explicit authorization to continue.
- Phase 0 is documentation only; Phase 1 foundation and Phase 2 acquisition are now implemented; a bounded live SEC ingestion/reuse/integrity check is recorded as passed. See docs/phase-2-review.md. Later-phase modules in architecture diagrams remain proposed. Documents that describe proposed modules or commands do not establish that those modules or commands exist.
- Each Codex cloud task already has an isolated environment. Use the existing checkout; do not create a Git worktree unless the user explicitly requests one. Use a feature branch or PR when available and appropriate; preserve the current branch and user work when changing it would be disruptive. Do not push or publish without authorization.

## Before implementation

1. Review the assigned package, its prerequisites, acceptance criteria, affected ADRs, and existing implementation.
2. Explain the plan: components, files, dependencies, contracts, tradeoffs, and checks. Ask only about decisions that block useful progress and cannot be inferred.
3. Define external contracts and important invariants before implementing components. Update an ADR when materially changing the architecture.
4. Prefer existing modules and repository-supported configuration. Never overwrite working implementation unnecessarily or create duplicate implementations.

## Engineering rules

- Keep Python domain logic independent of FastAPI, LangChain, LangGraph, and persistence adapters. Use explicit, typed interfaces and Pydantic validation at external boundaries.
- Start with a single research agent and bounded tools. Additional agents, Spark, Delta Lake, hybrid retrieval, reranking, and new infrastructure require a documented benefit and an evaluation or workload justification.
- Use deterministic decimal arithmetic and versioned policies for financial selection and calculation. Never delegate arithmetic or selection authority to an LLM.
- Preserve immutable Bronze artifacts and source checksums. Make processing idempotent and record pipeline, schema, selection-policy, and dataset versions.
- Preserve originally reported and later reported financial observations. Do not infer an observation's measurement period from its `fy` field. Enforce period, currency, unit, filing-date, dimensional, and historical as-of semantics.
- Treat retrieved text and model output as untrusted. Enforce tool permissions, authorization, network restrictions, and budgets in code. Verify citations against the evidence registry; abstain when evidence is inadequate.
- Use structured, recoverable errors. Redact secrets and sensitive content from logs and traces. Never commit credentials, keys, environment files with secret values, or unnecessary large datasets.
- Pin supported dependency versions and commit the relevant lockfiles when implementation begins. Avoid dependencies without a concrete benefit. Preserve TLS, signatures, and artifact checksums during setup.
- Separate demo behavior from production guarantees. Record debt, limitations, and unresolved issues in the affected documentation and package review.

## Verification and change control

- Write meaningful automated tests for new logic; run relevant tests after changes. Include failure paths and financial edge cases. Follow [testing](docs/testing-strategy.md) and [evaluation](docs/evaluation-strategy.md).
- Never claim an unexecuted check passed. Report passed, failed, skipped, expected failures, and unrun checks separately. Diagnose failures without silently weakening assertions.
- Update documentation whenever behavior, schemas, interfaces, or architecture change. Distinguish benchmark targets from measured results.
- Review the diff for unrelated changes, secret exposure, generated artifacts, and lockfile churn. Preserve existing user changes.
- Work through setup failures within authorized scope. Report concrete external blockers after completing independent work.

## Required package review

At every phase or package gate report:

1. Changes made and files created or modified.
2. Architecture decisions, alternatives, and deviations.
3. Commands actually run and their outcomes, including test counts when applicable.
4. Errors, unresolved issues, known limitations, and technical debt.
5. Acceptance criteria satisfied or outstanding.
6. The next recommended package, without starting it automatically.

Run `bash scripts/check.sh` for locked dependencies, lint/format, strict typing, and offline tests. With `TEST_DATABASE_URL` set to a dedicated database ending in `_test`, it runs the entire suite. Integration tests create/drop uniquely named databases and require a role with CREATEDB; never point them at a user/production database. Run `bash scripts/verify-wheel.sh` for distribution validation. See [development instructions](docs/development.md) for Compose/build/start commands. Do not invent passing results or implement later phases to satisfy a checklist.
