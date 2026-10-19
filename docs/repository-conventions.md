# Repository conventions

Status: proposed structure. Only the Markdown documentation exists in Phase 0. Paths in the tree below are implementation destinations, not created scaffolding.

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

Use `uv` for environment and dependency management with a committed `uv.lock`. Propose Python 3.12 as the initial compatibility target; Phase 1 must verify it against the selected dependency set before pinning. Use pytest, Ruff, and mypy; select and lock compatible versions in package 1A. Later introduce Next.js, TypeScript, an active supported Node LTS, and npm with `package-lock.json`; use `npm ci` in CI. No exact versions have been tested in Phase 0.

Dependency updates require lockfile review and relevant tests. Use frozen installation in CI. Avoid top-level import side effects, network calls during tests, and framework objects in domain contracts. API models use explicit field constraints and reject unexpected input where feasible.

## Repository hygiene

Track small, licensed or publicly sourced fixtures with provenance and checksums. Exclude local virtual environments, `.env` secrets, database volumes, downloaded filings, indexes, checkpoints, traces, benchmark output, build artifacts, and provider credentials. Add actual ignore rules with the Phase 1 tooling package; Phase 0 creates no generated artifacts in the checkout.

Commit migrations and schema versions, not live database state. Never edit published immutable source objects or historical dataset manifests in place. Keep derived local data outside the tracked source tree or in an explicitly ignored runtime directory.

Use descriptive feature branches and focused changes when a normal Git history is available. The initial checkout currently has an unborn `work` branch; a first commit and remote publication are separate authorized actions. Do not manufacture a remote branch or claim a PR exists.

## Documentation and change lifecycle

Every package follows audit → plan → implementation → verification → review → stop. Update the ADR index and related contracts for material changes. ADR statuses are Proposed, Accepted, Superseded, or Rejected; Phase 0 decisions are Proposed for implementation and are not evidence of working software.

API routes are versioned under `/v1`; data manifests, Pydantic schemas, prompts, formulas, and tool schemas carry independent versions. Breaking contract changes require migrations or an explicit compatibility window. Package reviews record implemented scope, test evidence, unresolved issues, and the next package.
