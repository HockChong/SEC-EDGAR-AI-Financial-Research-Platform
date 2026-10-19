# ADR-002 — Locked, reproducible development dependencies

Status: Accepted. Architecture: 3.1. Implementation phase: 1.

## Context

FastAPI/Pydantic, LangChain/LangGraph, database extensions, model adapters, and a Next.js frontend evolve independently. Unpinned environments obscure regressions and make benchmark comparisons unreliable.

## Decision

Use `pyproject.toml` with `uv.lock`, a pinned supported Python interpreter, and explicit development/evaluation dependency groups. Propose Python 3.12 pending compatibility checks in 1A. Use pytest, Ruff, and mypy. Commit lockfiles and use frozen installs in CI; pin uv and container/service versions after testing.

When the frontend is introduced, use TypeScript, Next.js, a supported Node LTS, npm and `package-lock.json`, with `npm ci`. Record tool versions in setup docs. Keep provider-specific and evaluation-only dependencies out of minimal runtime groups where feasible.

## Alternatives and consequences

pip-tools can provide a sound locked workflow but requires additional environment conventions. Poetry is viable but offers no established benefit for this empty repository. Unlocked pip requirements or floating container tags create avoidable reproducibility risk.

Exact pins require scheduled maintenance and security updates. A lockfile does not prove compatibility, artifact integrity, or reproducibility across every platform; CI must exercise the supported environment and preserve TLS/signature verification.

## Validation and reconsideration

Package 1A must demonstrate a clean frozen install, nonzero baseline tests, lint/type checks, and package build. Package 1B verifies PostgreSQL/pgvector and migrations. Add framework packages incrementally when their phases begin, preserving a compatible lock. Revisit tooling only for a documented packaging/platform problem, not preference alone.

## Phase 1 evidence

Python 3.12.14 and uv 0.12.23 are pinned with verified FastAPI/Pydantic, SQLAlchemy/psycopg, Alembic, pytest, Ruff, and mypy dependencies. `httpx2` is used by the current Starlette TestClient. Frozen installation, strict typing, nonzero tests, wheel/sdist creation, and a clean installed-wheel smoke check passed. Exact versions and commands are in [development](../development.md). Frontend dependencies remain deferred.
