# SEC EDGAR AI Financial Research Platform

An AI-first research platform designed to answer questions about public companies using SEC filings, structured XBRL facts, deterministic calculations, and verifiable citations.

**Status: Phase 2 ingestion and Phase 3 WP3.1–WP3.5 implemented.** Architecture version: **3.1**. The repository provides a typed Python package, safe configuration/logging, a health-only FastAPI service, PostgreSQL/pgvector development infrastructure, migrations, tests, and CI. SEC acquisition adds immutable Bronze storage, persistent manifests, discovery and a resumable CLI. Deterministic HTML parsing now produces source-linked sections and content blocks with opaque tables. Research, model integrations, financial calculations, and the frontend remain future work. See the [ingestion guide](docs/ingestion.md) and [WP3.2 review](docs/phase-3-wp3.2-review.md).

WP3.3 adds [structured table extraction](docs/table-extraction.md), separate
retrieval text, deterministic displayed-number normalization and multi-period
header tests. Codex leads development; hands-on assignments are paused.
Implementation is ready for package review; independent financial adjudication
remains required. See the [WP3.3 review](docs/phase-3-wp3.3-acceptance-review.md).

## Run the foundation

Prerequisites: Python **3.12.14**, uv **0.12.23**, Docker Engine and Compose v2. From the repository root:

```bash
bash scripts/setup.sh
bash scripts/start.sh
```

The API binds to loopback on port 8000. Check `/health/live` and `/health/ready` with a local HTTP client. Setup explicitly applies migrations; API startup does not migrate the database. See [development instructions](docs/development.md) for container startup, configuration, integration tests, and troubleshooting.

```bash
bash scripts/check.sh              # lint, format, strict typing, offline tests
bash scripts/verify-wheel.sh       # build and validate a wheel outside the checkout
```

The database uses public disposable development credentials and a persistent Compose volume. This foundation supports isolated development only; shared deployment and authentication are assigned to Phase 7.

## Intended research experience

> Compare Microsoft and Alphabet's revenue growth, operating margins, and capital expenditure trends over the past three fiscal years. Explain management's commentary and key risks, and cite the original filings.

The proposed workflow resolves companies and periods, retrieves filing evidence and financial observations, computes metrics in deterministic code, checks evidence, and returns a structured report. Missing or incompatible evidence produces a qualified result or abstention. Numerical claims must be traceable to selected observations and a versioned formula.

## Proposed architecture

- Python modular application; FastAPI service and Next.js research interface.
- Official SEC APIs and archives → immutable Bronze artifacts → validated Silver data → versioned Gold research datasets.
- PostgreSQL/pgvector serves metadata, financial facts, keyword and vector retrieval, and persistent research state.
- LangChain provides model, embedding, retrieval, and tool adapters; LangGraph manages one bounded research workflow.
- Local filesystem storage behind an object-store interface; Docker Compose for local services; managed infrastructure later.
- Baselines and evaluation gates precede hybrid retrieval, reranking, distributed processing, or additional agents.

See the [system overview](docs/architecture/system-overview.md) for component boundaries and diagrams.

## Read the design

| Document | Purpose |
| --- | --- |
| [Requirements](docs/requirements.md) | Product scope, constraints, and requirement traceability |
| [Repository conventions](docs/repository-conventions.md) | Proposed package tree and development workflow |
| [Technology decisions](docs/technology-decisions.md) | Choices, alternatives, costs, and adoption gates |
| [Data architecture](docs/architecture/data-architecture.md) | Ingestion, medallion processing, provenance, and reproducibility |
| [AI architecture](docs/architecture/ai-architecture.md) | Retrieval, research graph, tools, and report contract |
| [Deployment architecture](docs/architecture/deployment-architecture.md) | Local development, managed deployment, and observability |
| [Security architecture](docs/architecture/security-architecture.md) | Trust boundaries, access control, and abuse prevention |
| [Data dictionary](docs/data-dictionary.md) | Proposed entities, identifiers, types, and invariants |
| [ADR index](docs/adr/README.md) | Architecture decision records |
| [Testing strategy](docs/testing-strategy.md) | Test layers, fixtures, and CI requirements |
| [Evaluation strategy](docs/evaluation-strategy.md) | Datasets, metrics, baselines, and release gates |
| [Roadmap](docs/roadmap.md) | Phases 1–8, work packages, acceptance criteria, and effort estimates |
| [Phase 0 review](docs/phase-0-review.md) | Audit, completion checklist, risks, and recommended next package |
| [Development guide](docs/development.md) | Tested installation, configuration, services, migrations, and checks |
| [Phase 1 review](docs/phase-1-review.md) | Foundation implementation, verification evidence, and limitations |
| [AGENTS.md](AGENTS.md) | Instructions for future development agents |

## Development status and next step

Phase 1 implements packages 1A–1C. Dependencies are pinned in `pyproject.toml` and `uv.lock`; container images and CI actions are pinned to immutable digests/revisions. The CI workflow builds distributions and validates containers; cloud deployment automation remains in Phase 7.

Phase 2 implements SEC transport, company/filing discovery, immutable Bronze, Company Facts and recovery. The expanded corpus has 18 filings across five companies and 28 verified Bronze objects; see the [corpus review](docs/bronze-corpus-review.md). WP3.1 supplies canonical contracts. WP3.2 parses all 18 filings deterministically; 25 selected source-inspected boundaries match, with human adjudication still outstanding and quarterly JPMorgan Part I coverage gaps retained as warnings. See [HTML parsing](docs/html-parsing.md) and the [package review](docs/phase-3-wp3.2-review.md). WP3.3 table extraction and displayed-number normalization are implemented; see the [table guide](docs/table-extraction.md) and [WP3.3 review](docs/phase-3-wp3.3-acceptance-review.md). Independent financial adjudication and package acceptance remain open. WP3.4 now adds [Company Facts normalization and deterministic reported-fact selection](docs/xbrl-normalization.md); see the [WP3.4 review](docs/phase-3-wp3.4-review.md). WP3.3 financial adjudication was owner-deferred, not passed. WP3.5 adds [versioned Silver/Gold datasets](docs/dataset-publication.md), source-linked evidence and transactional PostgreSQL activation. See the [WP3.5 review](docs/phase-3-wp3.5-review.md). Review WP3.5 before explicitly authorizing WP3.6 chunking.

This is a portfolio project under development. Production readiness, financial accuracy, security, performance, and deployment are goals to demonstrate through evidence, not current guarantees.
