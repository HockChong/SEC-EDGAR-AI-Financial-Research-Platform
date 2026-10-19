# Repository conventions

Status: target structure with Phase 1 foundation implemented. The tree below includes future module destinations; only settings, contracts, the PostgreSQL adapter, observability, and health API are implemented so far. See [development](development.md) for current commands.

## Proposed layout

```text
.
├── AGENTS.md
├── README.md
├── pyproject.toml                 # Python metadata, tooling, dependency groups
├── uv.lock                       # exact resolved Python dependency set
├── .python-version               # selected supported interpreter
├── .env.example                  # documented non-secret examples
├── compose.yaml                  # local PostgreSQL/pgvector and app services
├── src/sec_research/
│   ├── domain/                   # entities, periods, units, financial policies
│   ├── contracts/                # Pydantic API, tool, data-boundary schemas
│   ├── application/              # use cases and interfaces (ports)
│   ├── ingestion/                # SEC fetch/discovery and ingestion orchestration
│   ├── processing/               # parsing, normalization, quality, dataset builds
│   ├── retrieval/                # search, fusion, evidence and citation services
│   ├── research/                 # graph state, nodes, budgets, tool routing
│   ├── evaluation/               # dataset loaders, metrics, benchmark runners
│   ├── adapters/
│   │   ├── sec/                  # HTTP transport and SEC contracts
│   │   ├── postgres/             # SQL repositories, pgvector, checkpoints
│   │   ├── storage/              # local and later object-store implementations
│   │   └── models/               # LangChain provider adapters
│   ├── api/                      # FastAPI routes, auth, exception mapping
│   ├── jobs/                     # durable job execution and leases
│   ├── observability/            # structured logs and tracing integration
│   └── settings.py
├── migrations/                   # Alembic migrations, separate from startup
├── tests/{unit,contract,integration,e2e}/
├── tests/fixtures/               # small reviewed fixtures and source manifests
├── evaluations/                  # versioned cases, annotations, run manifests
├── web/                          # Next.js application and its lockfile
├── scripts/                      # thin documented operational entry points
├── infra/                        # deployment definitions, added in Phase 7
├── .github/workflows/            # CI and eventually deployment
└── docs/
```

## Module boundaries

Domain functions accept ordinary typed values and return explicit results; they do not call frameworks, networks, databases, or LLMs. Application services depend on narrow protocols such as `ArtifactStore`, `FinancialFactRepository`, `EvidenceSearch`, `ResearchCheckpointStore`, and `ModelGateway`. Adapters implement those protocols. API routes, jobs, and graph nodes invoke application services rather than duplicating business rules.

Keep modules small enough to evolve without creating an interface for every class. Split only at actual substitution, transaction, or trust boundaries. Use SQLAlchemy and Alembic for persistence and migrations; isolated SQL is appropriate for full-text and vector queries. This is one Python package with API and worker entry points, not multiple independent services.

## Toolchain policy

Use `uv` 0.12.23 and Python 3.12.14 with the committed `uv.lock`. Phase 1 verifies pytest, Ruff, mypy, FastAPI/Pydantic, SQLAlchemy/psycopg, and Alembic together; exact direct dependencies are pinned in `pyproject.toml`. Later introduce Next.js, TypeScript, a supported Node LTS, and npm with `package-lock.json`; use `npm ci` in CI. No frontend tooling is installed in Phase 1.

Dependency updates require lockfile review and relevant tests. Use frozen installation in CI. Avoid top-level import side effects, network calls during tests, and framework objects in domain contracts. API models use explicit field constraints and reject unexpected input where feasible.

## Repository hygiene

Track small, licensed or publicly sourced fixtures with provenance and checksums. Exclude local virtual environments, `.env` secrets, database volumes, downloaded filings, indexes, checkpoints, traces, benchmark output, build artifacts, and provider credentials. Phase 1 supplies `.gitignore`, an allowlisted Docker build context, and an explicit source-distribution file allowlist.

Commit migrations and schema versions, not live database state. Never edit published immutable source objects or historical dataset manifests in place. Keep derived local data outside the tracked source tree or in an explicitly ignored runtime directory.

Use descriptive feature branches and focused changes. Phase 0 was committed and pushed to `main`; Phase 1 uses `feat/phase-1-foundation` locally. Do not push or publish without authorization, and do not claim a PR exists without evidence.

## Documentation and change lifecycle

Every package follows audit → plan → implementation → verification → review → stop. Update the ADR index and related contracts for material changes. ADR statuses are Proposed, Accepted, Superseded, or Rejected; Phase 0 decisions are Proposed for implementation and are not evidence of working software.

API routes are versioned under `/v1`; data manifests, Pydantic schemas, prompts, formulas, and tool schemas carry independent versions. Breaking contract changes require migrations or an explicit compatibility window. Package reviews record implemented scope, test evidence, unresolved issues, and the next package.
