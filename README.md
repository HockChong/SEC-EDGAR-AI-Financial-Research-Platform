# SEC EDGAR AI Financial Research Platform

An AI-first research platform designed to answer questions about public companies using SEC filings, structured XBRL facts, deterministic calculations, and verifiable citations.

**Status: Phase 0 planning complete; application implementation has not started.** Architecture version: **3.1**. The repository currently contains design and governance documents only. There is no running API, UI, ingestion pipeline, database, model integration, or benchmark result. No installation command is available yet.

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
| [AGENTS.md](AGENTS.md) | Instructions for future development agents |

## Development status and next step

Phase 0 introduces no runtime dependencies or application features. Python project metadata, a lockfile, Compose configuration, CI, and baseline tests belong to Phase 1. Exact tool and dependency versions must be selected and verified together in its first package.

Recommended next assignment: **Phase 1, package 1A — Python package and reproducible tooling**. Explicit authorization is required before starting that package. Each subsequent package also ends with a review gate; see the [execution rules](AGENTS.md) and [roadmap](docs/roadmap.md).

This is a portfolio project under development. Production readiness, financial accuracy, security, performance, and deployment are goals to demonstrate through evidence, not current guarantees.
