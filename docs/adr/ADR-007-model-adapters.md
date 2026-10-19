# ADR-007 — Provider abstraction through LangChain adapters

Status: Proposed. Architecture: 3.1. Implementation phases: 4–6.

## Context

Generation, embeddings, and optional reranking have different cost, latency, retention, and compatibility properties. Provider-specific SDK models should not become domain contracts, but over-generalizing before a baseline adds complexity.

## Decision

Use LangChain integration packages behind small application ports for structured generation and embeddings, and a separate reranking interface when justified. Begin with one provider selected in 4A using capability, quality, cost, retention, region, credential availability, and model-version stability. Record exact model IDs and embedding dimensions.

Configure credentials explicitly through approved runtime bindings. Enforce deadlines, retries, output validation, token/cost budgets, and usage logging in adapters. Provide a deterministic fake adapter for offline tests, labeled as simulated generation. Provider fallbacks are opt-in, recorded, and cannot silently change report semantics or privacy policy.

## Alternatives and consequences

Direct SDK calls are straightforward but couple use cases to provider response schemas and bypass the requested LangChain integration. A universal multi-provider platform adds unused complexity. Hosted inference reduces operations initially; local models may improve control but require hardware, serving, and separate quality evaluation.

LangChain introduces version churn and cannot guarantee interchangeable behavior. Changing embedding models requires a new index; changing generation models requires regression evaluation. Explicit typed adapters keep those changes contained.

## Validation and reconsideration

Test schema errors, timeout/throttling, token accounting, secret redaction, and unsupported model features. Verify one real provider smoke request when credentials are supplied securely; fake tests do not validate provider access or model quality. Add another provider only for a benchmark comparison or documented operational requirement.
