# ADR-003 — Immutable sources and reproducible research datasets

Status: Proposed. Architecture: 3.1. Implementation phases: 2–3.

## Context

SEC source responses and financial reportings change. Parsing and chunking also evolve. Research must be traceable to the exact data used, and retrieval indexes must not become the only surviving record of a filing or fact.

## Decision

Use Bronze/Silver/Gold boundaries:

1. Bronze retains immutable raw HTML/JSON bytes, SHA-256 identities, fetch manifests, source URLs, filing metadata, and ingestion outcomes.
2. Silver contains versioned normalized companies, filings, documents, sections, blocks, structured tables, XBRL concepts/observations, periods, provenance, and quality events.
3. Gold contains reproducible research chunks, evidence mappings, fact-serving datasets, versioned metric definitions, timelines, and catalogs.

Persist canonical normalized datasets as versioned Parquet plus immutable manifests. Use PostgreSQL for transactional catalog/job/checkpoint state and serving projections. Embeddings, vector/full-text indexes, and convenience views are derived and rebuildable. Atomically activate a fully validated snapshot; pin research to its version.

Start with Python and Arrow-based bounded processing. Defer Delta Lake until concurrent-writer, table-update, or time-travel requirements justify its operational cost. Defer Spark until representative workloads exceed documented memory/runtime goals despite batching, efficient formats, and profiling.

## Alternatives and consequences

A database-only approach is simpler initially but weakens immutable replay and large analytical interchange. An immediate Spark/Delta stack offers scalable transactions and batch processing but adds JVM/runtime maintenance without current workload evidence. A vector-only store loses authoritative structured lineage.

The chosen approach requires manifest/projection reconciliation and orphan recovery across object and SQL storage. Content deduplication must retain multiple fetch/provenance links. Publication, rollback, and garbage collection become explicit operations rather than ad hoc file replacement.

## Data semantics

Preserve original and later-reported observations separately. Measurement dates, filing availability, units, context, and reporting versions are independent fields. Company Facts missing dimensional metadata remains unknown. Parse tables and narrative with source locators; do not flatten away headers, scale, sign, or footnotes. Quality failures quarantine unsupported data rather than supplying invented defaults.

## Validation and reconsideration

Phase 2 tests repeated/failed downloads, hashes, manifests, compliance, and idempotency. Phase 3 tests varied filing fixtures, fiscal-period and context edge cases, source-resolvable chunks/facts, deterministic Bronze replay, and interrupted publication. Spark/Delta adoption requires a measured workload, comparison, operating plan, and a follow-up ADR.
