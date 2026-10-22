# Architecture decision records

All records began as **Proposed** in Phase 0. Phase 1 accepts ADR-001/002 and the local-development portion of ADR-008 with validation evidence. Phase 2 implements the Bronze portion of ADR-003 and accepts ADR-010; a bounded user-executed live smoke check passed. Other records remain proposed implementation directions. Preserve superseded records with a link to their replacement; accepted direction does not imply later-phase functionality exists.

| ADR | Decision | Primary delivery |
| --- | --- | --- |
| [ADR-001](ADR-001-modular-application.md) | Modular Python application and dependency boundaries | 1 |
| [ADR-002](ADR-002-dependency-management.md) | Reproducible toolchain and locked dependencies | 1 |
| [ADR-003](ADR-003-data-pipeline.md) | Immutable Bronze, versioned Silver/Gold, source-resolvable data | 2–3 |
| [ADR-004](ADR-004-retrieval.md) | PostgreSQL/pgvector and evaluated retrieval stages | 4 |
| [ADR-005](ADR-005-research-orchestration.md) | One bounded LangGraph research workflow | 5 |
| [ADR-006](ADR-006-financial-correctness.md) | Deterministic fact selection and calculation | 3, 5 |
| [ADR-007](ADR-007-model-adapters.md) | LangChain-backed provider abstraction | 4–6 |
| [ADR-008](ADR-008-deployment-security.md) | Local Compose, managed deployment, application security | 1, 7 |
| [ADR-009](ADR-009-evaluation.md) | Versioned benchmarks and explicit quality gates | 3–6 |

[ADR-010](ADR-010-bronze-coordination.md) records Phase 2 shared rate coordination, immutable publication and provenance-preserving rollback.

Each record states context, decision, alternatives, consequences, validation, and triggers for reconsideration. Significant departures require an updated or superseding ADR before implementation expands.
