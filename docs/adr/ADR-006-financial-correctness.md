# ADR-006 — Deterministic selection and financial calculations

Status: Proposed. Architecture: 3.1. Implementation phases: 3 and 5.

## Context

The same measurement period can appear in multiple filings with different values. SEC fiscal-year labels, cumulative quarters, unknown dimensions, incompatible currencies, and overlapping concept definitions can yield plausible but incorrect calculations.

## Decision

Separate preservation, eligibility, selection, and calculation. Preserve every source reporting; select through a versioned policy; calculate with Decimal and a versioned formula catalog. The model may request a supported metric but cannot decide arithmetic, silently choose a candidate, or submit arbitrary expressions.

Selection order:

1. Restrict to the requested CIK, dataset, approved metric/concept mappings, and eligible source/form.
2. Require compatible actual measurement dates, period kind, verified context, and unit/currency. Reject unresolved context when it affects the metric.
3. Enforce availability cutoff using accepted timestamps where present and explicitly documented end-of-day semantics for date-only evidence.
4. Apply `original`, `latest_as_of`, or `compare_versions` reporting mode; retain repeated/later observations and amendment relationships.
5. Apply documented metric-specific concept priority among equivalent candidates. Deduplicate exact equivalents, but surface unresolved conflicts as ambiguity; never break ties by row order.
6. Return selected IDs, eligibility/ranking reasons, alternatives, warnings, and policy version.

Metrics validate input compatibility before calculation. Use exact decimal values and explicit denominator, sign, scale, rounding, and percentage-point policies. Derived Q4 requires compatible annual and nine-month cumulative observations; maintain its derivation chain. Cross-company fiscal periods remain explicitly labeled when they do not align.

## Alternatives and consequences

Selecting the latest row by `fy` or averaging conflicting facts is simple and financially unsound. LLM arithmetic and implicit concept matching are flexible but non-reproducible. Universal concept mappings overstate comparability across issuers.

Conservative eligibility creates more abstentions, especially when Company Facts omits context. This is preferable to hidden assumptions. Expand supported concepts/context extraction through reviewed cases and explicit policies, preserving prior results and policy versions.

## Validation and reconsideration

Require exact tests for original/later values, amendments, as-of cutoffs, unknown context, units/currencies, non-calendar/53-week years, YTD versus quarter, instant versus duration, zero/nonpositive denominators, negative values, rounding, and conflicting concepts. Every output must reproduce from recorded inputs. Expand scope only with curated ground truth and updated metric contracts.
