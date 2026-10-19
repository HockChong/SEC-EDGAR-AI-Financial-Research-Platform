# ADR-005 — One bounded, durable LangGraph research workflow

Status: Proposed. Architecture: 3.1. Implementation phase: 5.

## Context

Questions combine narrative retrieval, financial lookup, deterministic computation, and synthesis. A free-running agent can exceed budgets, repeat calls, lose progress, and convert untrusted evidence into instructions.

## Decision

Use an explicit LangGraph workflow with one research agent and specialized tools. Nodes perform query understanding, planning, routing, retrieval/fact lookup, calculation, evidence validation, synthesis, and final verification. Pydantic validates plans, tool contracts, state boundaries, and reports.

Enforce allowlists, authorization, deadlines, retry/repair limits, token/cost budgets, and cancellation in application code. Persist versioned checkpoints and job leases in PostgreSQL; keep durable worker execution separate from API request lifetime. Store report versions independently of mutable checkpoints.

## Alternatives and consequences

A custom state machine avoids framework coupling but requires writing checkpoint/recovery tooling. Unbounded agent loops are flexible but difficult to audit. Multiple agents add coordination, latency, and evaluation complexity without a current demonstrated benefit.

LangGraph requires explicit state-schema and library-version compatibility. Checkpoints do not make external model calls exactly once; track request/usage outcomes and bound duplicate execution after crashes. A durable lease is still needed to prevent simultaneous workers from resuming one run.

## Validation and reconsideration

Test success, missing/conflicting evidence, tool rejection, retry/budget exhaustion, cancellation, worker termination/resume, lease races, and invalid checkpoint migration. Compare task success and cost against the Phase 4 RAG baseline. Introduce additional agents only after an evaluated task limitation and measured improvement justify them.
