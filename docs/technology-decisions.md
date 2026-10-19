# Technology decision matrix

Phase 1 verifies and pins foundation choices; see [development](development.md) for exact versions. Later-phase selections remain proposed and require validation in their assigned packages. This matrix summarizes rationale; ADRs contain decision details.

| Area | Proposed choice | Alternatives and tradeoff | Adoption or revisit condition |
| --- | --- | --- | --- |
| Python layout | One `src/sec_research` package with domain, application, and adapters | Flat scripts start faster but obscure boundaries; independent services add deployment cost | Split only after demonstrated independent scaling or ownership need; ADR-001 |
| Python dependencies | `uv`, `pyproject.toml`, committed `uv.lock`, Python 3.12 candidate | pip-tools is viable; Poetry adds a different workflow without a current project benefit | Verify Python/framework/driver compatibility in 1A; ADR-002 |
| Web dependencies | Next.js + TypeScript, npm lockfile, supported Node LTS | Python-only UI is quicker but less suitable for the specified research experience | Add thin UI in 5C, polish in 8; no frontend runtime in Phase 0 |
| API and contracts | FastAPI + Pydantic; shared domain logic | Django provides more built-ins; Flask requires more manual validation | FastAPI matches typed research contracts; keep SDK models out of domain |
| SQL and migrations | PostgreSQL, SQLAlchemy, psycopg, Alembic | SQLite cannot faithfully validate PostgreSQL vector/search behavior | Real PostgreSQL integration tests; migrations run explicitly |
| Retrieval database | PostgreSQL full-text + pgvector | Separate vector engine can scale differently but duplicates metadata and filtering | Benchmark recall, filter behavior, memory, and latency before considering another database; ADR-004 |
| Canonical storage | Immutable object files + versioned Parquet datasets + PostgreSQL serving projections | Database-only simplifies small data but weakens replay and batch interchange | Manifest and checksum lineage required; ADR-003 |
| Delta Lake | Deferred, compatible future dataset adapter | Adds transaction/time-travel capability but also runtime and table maintenance cost | Adopt for proven multi-writer transactions, reliable table updates, or large-scale time travel; ADR-003 |
| Spark | Deferred; Python/Arrow-based single-machine processing first | Spark benefits large shuffles; adds JVM, distributed operation, and local setup burden | Adopt after representative workload exceeds memory/runtime limits despite batching; document measurements |
| HTML extraction | Beautiful Soup/lxml candidates plus SEC-aware extraction logic | Generic text extraction loses table/section evidence; full browser rendering is expensive | Compare parser fixtures and malformed filings in 3A; no assumption of uniform SEC HTML |
| Models and embeddings | LangChain integrations behind application ports | Direct SDKs simplify individual calls but bypass the requested integration layer | Begin with one hosted provider; keep provider-specific data in adapters; ADR-007 |
| Orchestration | Explicit LangGraph workflow, one research agent | Free-form loops are hard to audit; custom FSM is possible but duplicates checkpoint tooling | Bounded nodes/tools and durable state required; ADR-005 |
| Retrieval quality | Dense baseline → keyword comparison → rank fusion → optional reranker | BM25/full-text alone is cheaper; dense alone can miss exact names/numbers | Promote added stages only on held-out relevance and operational evidence; ADR-004 |
| Financial engine | Decimal arithmetic, policy-driven fact selection, versioned formula catalog | LLM arithmetic is nondeterministic; float introduces avoidable precision errors | Exact calculation and period/unit tests mandatory; ADR-006 |
| Jobs | PostgreSQL job records, leases, idempotency, separate worker process from same package | In-process background tasks lose work; Redis/Celery adds infrastructure | Implement when long-running research begins; queue replacement requires load evidence |
| Evaluation | Versioned cases + pytest and explicit metric functions; optional Ragas adapter | Framework scores accelerate experiments but can hide definitions and judge variance | Retain raw outputs and metric definitions; optional evaluation tracing service only with privacy/cost review; ADR-009 |
| Observability | Structured logs + OpenTelemetry-compatible spans and metrics | Proprietary-only tracing creates coupling; logging prompts by default leaks data | Redacted metadata first, configurable OTLP export in deployment phase |
| Local deployment | Docker Compose, PostgreSQL/pgvector, local artifact storage | Fully managed development increases external dependencies; embedded substitutes differ from production | Containers or documented native fallback validated in Phase 1; ADR-008 |
| Cloud deployment | Managed PostgreSQL/pgvector, object storage, managed container platform | VM operations are flexible but manual; Kubernetes is premature | Provider/region selected using cost, residency, extension support, and restore tests in Phase 7 |
| Security | App-enforced access control, allowlisted tools/network, injection tests, secret manager | Prompt-only controls cannot authorize requests | Local unauthenticated mode restricted to isolated development; authentication before shared exposure; ADR-008 |

## Open choices with owners and deadlines

The assigned package implementer resolves each choice, records evidence, and updates its ADR during review.

- **1A/1B:** exact Python, uv, PostgreSQL, pgvector, and dependency versions; container availability; migration/checkpoint compatibility. Pin verified versions rather than `latest`.
- **2A:** compliant SEC organization/contact identity supplied through secure environment configuration; current official SEC access policy and endpoint behavior verified at implementation time.
- **3A/3B:** parser fidelity, dimensions unavailable in Company Facts, and metric concept allowlists on selected fixtures. Fail closed where public API data lacks required context; do not invent dimensions.
- **4A:** first model and embedding provider, model IDs, embedding dimension, retention terms, account access, and initial cost budget. Record a baseline before provider comparison.
- **5A:** durable checkpoint library and schema integration, maximum execution budgets, and cancellation semantics verified with recovery tests.
- **6A:** independently annotated evaluation sets and calibrated quality thresholds; target values are not results.
- **7A:** cloud provider, region, identity provider, budget, workload SLOs, and retention/recovery policy.

No API credentials, cloud deployment, live SEC data, or runtime service is required to review Phase 0.
