# ADR-009 — Explicit benchmarks and evidence-based optimization

Status: Proposed. Architecture: 3.1. Implementation phases: 3–6.

## Context

Plausible generated answers and impressive demonstrations do not establish financial correctness, citation support, robust retrieval, or useful agent behavior. Framework scores can conceal denominator choices, weak labels, and judge variance.

## Decision

Use a repository-owned, versioned case schema and explicit metric functions, with pytest for deterministic invariants and a separate benchmark runner for model/retrieval quality. Keep source snapshots, labels, splits, model/prompt/config versions, raw results, and costs reproducible. Establish baselines before optimization; compare variants on frozen held-out cases.

Use deterministic checks for calculations, selection, units, periods, source resolution, and authorization. Use reviewed rubrics and human calibration for semantic support/correctness. Optional Ragas or another evaluation adapter may assist but cannot replace definitions, evidence, or adjudication. Track retrieval, generation, finance, agent, and operational metrics separately.

## Alternatives and consequences

Manual demos are quick but nonrepeatable and selective. An evaluation framework alone speeds integration but may introduce opaque defaults or model-judge dependence. A fully custom harness costs implementation effort but makes critical financial and evidence semantics explicit; adapters can reduce commodity work later.

Annotation and maintenance require time. Small early datasets support diagnosis, not sweeping claims. Budgeted live evaluations may be separate from deterministic CI, but failures and skips must remain visible. Security/financial invariants cannot be averaged away by a good aggregate score.

## Validation and reconsideration

Test metric calculations against known examples, audit split leakage, calibrate judges, reproduce baseline reports, and publish case-level errors and uncertainty. Promote optimizations only under predeclared quality/latency/cost gates. Revisit framework choice if maintenance cost outweighs transparency benefits while preserving contracts and historical comparability.
