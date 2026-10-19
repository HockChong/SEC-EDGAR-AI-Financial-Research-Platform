# ADR-004 — PostgreSQL retrieval with measured optimization

Status: Proposed. Architecture: 3.1. Implementation phase: 4.

## Context

Research requires semantic and exact-term retrieval with company, form, period, and historical availability filters. A separate vector platform would duplicate metadata and access-control concerns before scale is known.

## Decision

Use PostgreSQL full-text search and pgvector behind a LangChain-compatible retrieval adapter. Establish a dense baseline and keyword comparison before evaluating reciprocal rank fusion and an optional bounded reranker. Keep evidence registry IDs and canonical datasets independent of the index.

Version embeddings by model/dimension, text hash, dataset, and chunker. Enforce scope and historical predicates through every retrieval and context-expansion path. Begin with exact search where the dataset permits; use approximate indexing only after measuring recall, filter selectivity, memory, and latency.

## Alternatives and consequences

Keyword-only search is cheap and strong for exact terms but can miss paraphrases. Dense-only retrieval can miss identifiers and precise numerical language. Hybrid/reranking can improve quality but increase latency, cost, and tuning complexity. An external search/vector service may scale differently but adds infrastructure and synchronization failure modes.

PostgreSQL combines metadata and retrieval operations but requires query/index tuning and connection/resource budgeting. Approximate vector filtering can return too few candidates; use tested settings or an exact filtered fallback rather than broadening the requested scope.

## Validation and reconsideration

Compare Recall@K, nDCG@K, MRR, filter correctness, and latency on the same frozen cases. Promote fusion/reranking only after held-out benefit meets a predeclared practical threshold and operational budgets. Reconsider a separate engine when measured PostgreSQL limitations remain after tuning and the added service has a justified migration plan.
