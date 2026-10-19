# Evaluation strategy

Status: design and proposed targets only. **No dataset, benchmark, provider comparison, score, latency, or cost result has been produced in Phase 0.**

## Evaluation system

Use versioned cases, source manifests, independent annotations, explicit metric functions, a runner over application interfaces, and immutable run reports. Establish a baseline at each capability's introduction; Phase 6 consolidates rather than postpones all evaluation. [ADR-009](adr/ADR-009-evaluation.md) records the framework tradeoff.

Each case records case ID/version, question, CIKs, actual periods, historical cutoff, dataset snapshot, task type, relevant evidence IDs with graded relevance, expected claims or abstention, required input observations/formulas, units, tolerances, annotation provenance, and source hashes. Never use an LLM-generated answer as unreviewed financial ground truth.

## Dataset plan

Proposed minimum development milestones, subject to corpus coverage and annotation effort:

- Phase 3/4: 30 manually reviewed retrieval questions across at least 5 issuers, including two-company comparisons, non-calendar fiscal years, narrative risks, exact terms, and tables.
- Phase 5: 25 deterministic financial cases covering period/context/unit and historical-reporting ambiguity, plus 20 multi-step research tasks with explicitly scored completion criteria.
- Phase 6: expand held-out evaluation to at least 100 retrieval/generation cases, 50 financial cases, and 30 agent tasks; add a separate adversarial set with at least 20 injection/authorization/budget cases. Counts are targets, not current assets.

Split by company, filing/time block, and question family to limit leakage. Do not place near-duplicate chunks/questions from the same disclosure in development and test sets. Reserve a held-out temporal set for historical selection. Small early sets are diagnostic; report uncertainty and avoid claims of generalization.

Development split tunes prompts, fusion, candidate sizes, and reranking. Freeze test splits before comparisons. Independent reviewers adjudicate disputed labels, especially support and financial concept equivalence. Record annotator disagreement and corrected dataset versions. Keep negative, missing-evidence, ambiguous-company, unsupported-metric, and abstention cases visible rather than dropping them.

## Metric definitions

| Area | Metric | Definition and interpretation |
| --- | --- | --- |
| Retrieval | Recall@K | Relevant evidence IDs in top K / all labeled relevant IDs; report no-relevant cases separately |
| Retrieval | nDCG@K | Discounted graded relevance normalized by ideal ranking; publish gain scale and treatment of duplicates |
| Retrieval | MRR | Mean reciprocal rank of first relevant hit; zero when no hit exists for an answerable case |
| Retrieval | Latency | Search wall time, p50/p95, with index size, filters, concurrency, and warm/cold state |
| Generation | Answer correctness | Rubric-based correctness per required claim/task, with human adjudication on sampled and disputed cases |
| Generation | Citation precision | Attached citations that support their associated claim / attached citations; zero citations on a claim requiring evidence must not be a vacuous pass |
| Generation | Groundedness | Supported factual claims / all factual claims, using resolved source evidence |
| Generation | Unsupported claim rate | Unsupported factual claims / all factual claims; report contradictions and missing citations separately |
| Finance | Numerical exact match | Exact decimal agreement after the specified formula and display policy; tolerances only when predeclared by the metric |
| Finance | Period and unit correctness | Share of evaluated results with correct measurement intervals, availability, scope, units, and currency; report each separately |
| Finance | Calculation validity | Correct formula, selected observations, denominator/sign policy, and traceable result |
| Agent | Task success | All required task outcomes achieved or correct abstention under the case rubric |
| Agent | Tool-call success | Valid tool calls returning their documented successful outcome / executed valid calls; correct typed missing-data outcomes reported separately |
| Agent | Invalid tool attempts | Count/rate of schema, permission, scope, or allowlist violations proposed or executed; executed unauthorized calls must remain zero |
| Agent | Recovery success | Injected recoverable failures correctly resumed / injected recoverable scenarios |
| Agent | Steps per task | Distribution of graph steps/tool invocations and budget exhaustion by task type |
| Production | Latency/error/throughput | End-to-end p50/p95, unsuccessful requests/attempts, completed tasks per time unit at declared concurrency |
| Production | Tokens/cost | Input/output tokens, embedding/reranker usage, retries, estimated charge with model/pricing version; distinguish measured billing from estimates |

Report denominators and exclusions for every metric. Empty denominators are not perfect scores. Compute answerable-case quality separately from abstention precision/recall and coverage; a system that always abstains cannot pass task success. Citation coverage and precision are separate checks.

## Baselines and experiments

1. Freeze a corpus, query set, relevance labels, and retrieval configuration. Compare dense and keyword baselines.
2. Evaluate hybrid fusion on the same cases; add reranking only if the benefit exceeds a predeclared practical improvement margin without violating cost/latency budgets.
3. Compare retrieval-only RAG against the research graph on tasks requiring financial lookup and calculations. Account for additional tokens, time, errors, and recovery.
4. Compare provider/model or prompt variants with identical source snapshots, tool policies, and budgets. Record temperature/seed where supported without promising deterministic generation.
5. Test caching only after measuring hit rate and correctness under snapshot, actor scope, cutoff, policy, prompt, and model changes. Never reuse a user-private result across access scopes.

Use paired per-case results and confidence intervals/bootstrap estimates when sample size permits. Publish regressions by task slice, not only a single average. Select a practical improvement margin and budget before running the final held-out comparison; do not move gates afterward to justify an optimization.

## Proposed release gates

These are intended targets to calibrate in Phase 6, not measured achievements or guarantees:

| Capability | Proposed gate |
| --- | --- |
| Provenance and filters | 100% source resolution and no company/as-of/access leakage on mandatory deterministic cases |
| Deterministic finance | 100% correctness on the finite mandatory selection/calculation suite; undefined or ambiguous cases handled according to policy |
| Retrieval | Recall@10 ≥ 0.85 on the frozen initial benchmark, plus slice review; threshold revisited transparently if labeling/corpus scope changes |
| Generated support | Citation precision ≥ 0.95 and unsupported claim rate ≤ 0.02 on adjudicated cases; all critical numerical claims traceable |
| Research graph | Task success ≥ 0.80 on the held-out initial task set, with separate answerable and abstention results |
| Security | Zero executed unauthorized operations, secret exposures, or cross-user disclosure in the mandatory adversarial suite |
| Operational | Enforce finite deadlines/usage limits; choose measured p95 and cost budgets for the selected workload/provider before shared release |

Hard correctness and security invariants are release blockers. Average model quality cannot override them. Broad performance promises require representative load and larger datasets; passing these finite tests does not prove universal correctness.

## Judge models and framework use

Prefer deterministic scoring for citations, selection, calculations, periods, units, schemas, and access boundaries. Human-reviewed rubrics establish semantic correctness/support. An optional Ragas or equivalent adapter may assist semantic metrics, but retain case-level inputs, judge model/prompt/version, scores, and rationales safe for review. Calibrate judge agreement against human labels; report disagreement and judge variance. Do not grade a model's unsupported answer solely with its own uncalibrated judgment.

## Run artifacts and reproducibility

Each evaluation report includes run ID/time, code revision, dependency lock hash, dataset/split hashes, source/index versions, model/provider/prompt versions, tool/selection/formula versions, hardware/service configuration, concurrency, limits, raw case results, failures/skips, aggregate metrics, cost estimate method, and comparison to a named baseline. Store large outputs outside Git with an immutable manifest; commit small summaries and reproducible commands when implemented.

Phase 6 acceptance requires actual reproducible results and a comparison report, not just a runner. Phase 8 portfolio claims must link to those measured reports and state their dataset and operating limits.
