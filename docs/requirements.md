# Project requirements — architecture 3.1

Status: proposed implementation specification established in Phase 0. Nothing in this document asserts implemented functionality.

## Product objective

Build an AI-first SEC research application for equity analysts, financial analysts, investment teams, corporate strategists, and financial consultants. Users ask research questions, inspect evidence and calculations, follow progress, and receive auditable reports. The financial data platform supports this research experience.

The primary scenario is a multi-company, multi-year comparison of revenue growth, operating margin, and capital expenditure, grounded in 10-K/10-Q disclosures and XBRL facts. The system must reconcile quantitative results with narrative evidence and explicitly identify uncertainty, disagreements, and unavailable data.

## Functional requirements and ownership

| ID | Requirement | Primary design | Delivery phase |
| --- | --- | --- | --- |
| R01 | Resolve company identities and discover 10-K/10-Q filings from official SEC sources | Data architecture; company and filing contracts | 2 |
| R02 | Download source artifacts with compliant identification, bounded access, integrity checks, and immutable storage | ADR-003; ingestion design | 2 |
| R03 | Normalize HTML sections, paragraphs, tables, XBRL observations, periods, and provenance | ADR-003; data dictionary | 3 |
| R04 | Produce versioned, reproducible Gold chunks, fact-serving datasets, and evidence registries | Data architecture | 3 |
| R05 | Retrieve relevant evidence using dense and keyword baselines, explicit metadata filters, and verified citations | AI architecture; ADR-004 | 4 |
| R06 | Execute a stateful, bounded research workflow using LangGraph and typed LangChain tools | AI architecture; ADR-005 | 5 |
| R07 | Select financial facts and calculate metrics deterministically with auditable inputs, units, and policies | ADR-006; financial contracts | 3, 5 |
| R08 | Return structured research reports with claims, citations, calculation evidence, limitations, and abstention | AI architecture | 4, 5 |
| R09 | Evaluate retrieval, generation, finance, agent behavior, security, cost, and latency reproducibly | Evaluation strategy; ADR-009 | Incremental; consolidated in 6 |
| R10 | Provide FastAPI research APIs and a Next.js interface for questions, progress, evidence, and reports | System and deployment architecture | API 4; UI 5; polish 8 |
| R11 | Authenticate and authorize users and protect jobs, evidence access, and operational resources | Security architecture; ADR-008 | Before shared deployment in 7 |
| R12 | Deploy with tracing, logging, CI/CD, recovery procedures, quotas, and measured operational limits | Deployment architecture | 7 |

## Required properties

- **Evidence:** every material factual claim identifies supporting evidence or is marked unsupported and excluded from the final supported answer. Source existence and semantic support are separate checks.
- **Financial correctness:** code chooses facts and performs arithmetic. Selection rejects incompatible periods, units, currencies, dimensional scope, or accounting definitions; ambiguity cannot become a silently selected value.
- **Point-in-time behavior:** historical availability is bounded by filing publication time and available metadata, not merely the observation period. Date-only SEC data supports end-of-day analysis; intraday certainty requires acceptance timestamps.
- **Reproducibility:** reports identify a dataset snapshot, pipeline versions, retrieval configuration, prompt/model versions, selection policy, evidence IDs, and formula versions. Model-generated text may vary; its recorded inputs and trace must be reproducible.
- **Reliability:** ingestion and processing are idempotent; retries are bounded; immutable inputs and restart-safe work records enable recovery.
- **Security:** authorization and network access are enforced outside prompts. Documents cannot instruct the application to execute arbitrary operations or reveal secrets.
- **Maintainability:** modular code, pinned dependencies, explicit contracts, migrations, meaningful tests, and versioned architecture decisions.
- **Measurement:** latency, usage, cost, quality, and failure behavior are measurable. Numeric budgets begin as proposed targets in the evaluation strategy and become release criteria after baseline measurement.

## Scope boundaries

Initial supported research focuses on US GAAP domestic registrants with 10-K/10-Q filings, USD monetary values, and explicitly identified consolidated contexts. Preserve other observations during ingestion, but mark unsupported semantics in serving results. Foreign issuers, IFRS reconciliation, 20-F/6-K, market prices, currency conversion, portfolio advice, and trading execution are outside the initial scope.

Annual and quarterly periods must be modeled separately. Prioritize annual revenue, operating income, and cash capital expenditures before expanding the metric catalog. Capex definitions vary; the chosen concept and exclusions must be visible.

Do not add Kubernetes, Kafka, extra databases, microservices, or distributed processing without an ADR and measurable need. Do not use unauthorized scraping. Providers, deployment region, service-level commitments, and final dependency versions remain explicit implementation decisions; they do not block Phase 0.

## Phase 0 acceptance

- Audit the checkout and preserve existing work.
- Document all eleven architecture areas specified by the project brief.
- Record material technology choices, alternatives, and consequences.
- Define contracts, lineage, financial selection, evaluation, and security constraints.
- Provide a phased roadmap with work packages, dependencies, proposed paths, tests, risks, effort, acceptance, and definitions of done.
- Create README, AGENTS, architecture documents, ADRs, and testing/evaluation guidance.
- Verify documentation coherence and report actual checks.
- Stop before Phase 1; no application features, dependencies, or runtime readiness claims.
