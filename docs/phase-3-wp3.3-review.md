> Historical structural-scaffold review. Superseded by the
> [WP3.3 completion and acceptance review](phase-3-wp3.3-acceptance-review.md).
> Hands-on assignments are paused and the numeric/header implementation is complete.
> Earlier learner gates and next-step instructions below are historical, not active.

# WP3.3 implementation review — financial table extraction

Review date: **2026-10-21**, Asia/Kuala_Lumpur. Architecture **3.1**.
Branch retained: `feat/sec-ingestion-html-parsing`. No commit, push or publication.

## Gate decision

**INCOMPLETE — structural implementation and diagnostics delivered; numeric
normalization and the owner-written header test remain reserved.** Passing
structural checks does not establish financial correctness. WP3.4 is not ready
to begin and has not started. Human table/section adjudication remains pending.

## Measured corpus results

The final [diagnostics](phase-3-wp3.3-diagnostics.json) record source/lock/code hashes,
per-filing counts and logical output hashes. Full outputs remain ignored under
`.runtime/wp33/final-documents`; Bronze was never rewritten or reacquired.

- **18/18 filings** processed and replayed identically; five companies, eight 10-Ks
  and ten 10-Qs. No document extraction failures.
- **2,472 visible tables detected and reconstructed**, including the 2,427
  WP3.2 opaque table blocks and 45 additional layout-heading tables. Zero corpus
  tables quarantined. Nested/malformed cases are exercised synthetically; this
  real corpus has 0 visible nested tables under the recovered-DOM policy.
- **1,211 predicted financial tables:** 89 statements,
  1,122 disclosures. **1,261 predicted nonfinancial
  tables:** 548 layout, 470 narrative, 243 TOC.
  These are heuristic categories, not independently verified classifications.
- **300,260/300,260 source cells** independently enumerated and resolved;
  raw visible lexical text and original rowspan/colspan attributes match source.
  Original source SHA-256/byte length, CIK/accession/filename and document links
  are checked through the existing source bridge and validated result envelope.
- **123,913 merged cells**, **22,630 header cells**,
  **152,358 cells with column-header links**, and
  **125,171 cells with reporting-period labels**.
  These measure reconstructed structure, not association accuracy. Periods remain
  source labels; no calendar interval or filing-date-based period is invented.
- **1,346 tables** retained from unclassified/ambiguous sections.
- **28 Bronze fetches and 28 objects** audited before and after; no orphans or
  changes. Repeated extraction and validated JSON round-trips passed for all 18.
- **25 review candidates**, five per company, prepared for independent human
  adjudication: income/balance/cash-flow, merged/multi-period and both JPMorgan
  quarters. See [candidate review](phase-3-wp3.3-adjudication.md). Expected judgments
  remain null. No precision, recall, accuracy or independent human agreement claimed.
- All **300,260 cell normalization results remain pending**; no parsed Decimal
  financial values or completed financial normalization gate is claimed.

## JPMorgan and per-filing register

Both problematic quarterly filings preserve the WP3.2 Part I Items 1/2 limitation.
Table extraction never requires known item metadata; it does not relabel those
sections. The first quarter has 270 tables / 39,082 cells; the second quarter has
279 tables / 52,678 cells. Their unknown/ambiguous-section table counts are 267 and
276 respectively. Source and replay checks pass for both.

- `0000320193-26-000013` / CIK 0000320193 / 10-Q: 39 tables; 4,702 cells; 13 tables in unknown/ambiguous sections; replay passed.
- `0001018724-26-000004` / CIK 0001018724 / 10-K: 92 tables; 7,139 cells; 11 tables in unknown/ambiguous sections; replay passed.
- `0000950170-25-100235` / CIK 0000789019 / 10-K: 85 tables; 19,065 cells; 8 tables in unknown/ambiguous sections; replay passed.
- `0001652044-25-000014` / CIK 0001652044 / 10-K: 184 tables; 9,934 cells; 17 tables in unknown/ambiguous sections; replay passed.
- `0001652044-26-000071` / CIK 0001652044 / 10-Q: 94 tables; 10,317 cells; 13 tables in unknown/ambiguous sections; replay passed.
- `0001193125-26-191507` / CIK 0000789019 / 10-Q: 59 tables; 18,630 cells; 7 tables in unknown/ambiguous sections; replay passed.
- `0001018724-26-000026` / CIK 0001018724 / 10-Q: 54 tables; 5,943 cells; 9 tables in unknown/ambiguous sections; replay passed.
- `0001652044-26-000018` / CIK 0001652044 / 10-K: 185 tables; 10,015 cells; 16 tables in unknown/ambiguous sections; replay passed.
- `0001628280-26-008131` / CIK 0000019617 / 10-K: 679 tables; 56,769 cells; 631 tables in unknown/ambiguous sections; replay passed.
- `0001628280-26-029344` / CIK 0000019617 / 10-Q: 270 tables; 39,082 cells; 267 tables in unknown/ambiguous sections; replay passed.
- `0001018724-26-000014` / CIK 0001018724 / 10-Q: 54 tables; 4,072 cells; 9 tables in unknown/ambiguous sections; replay passed.
- `0001193125-26-323660` / CIK 0000789019 / 10-K: 88 tables; 19,803 cells; 8 tables in unknown/ambiguous sections; replay passed.
- `0001193125-26-027207` / CIK 0000789019 / 10-Q: 59 tables; 17,942 cells; 7 tables in unknown/ambiguous sections; replay passed.
- `0001652044-26-000048` / CIK 0001652044 / 10-Q: 86 tables; 6,759 cells; 13 tables in unknown/ambiguous sections; replay passed.
- `0000320193-25-000079` / CIK 0000320193 / 10-K: 62 tables; 6,411 cells; 14 tables in unknown/ambiguous sections; replay passed.
- `0001628280-26-054343` / CIK 0000019617 / 10-Q: 279 tables; 52,678 cells; 276 tables in unknown/ambiguous sections; replay passed.
- `0000320193-26-000020` / CIK 0000320193 / 10-Q: 40 tables; 4,730 cells; 13 tables in unknown/ambiguous sections; replay passed.
- `0000320193-24-000123` / CIK 0000320193 / 10-K: 63 tables; 6,269 cells; 14 tables in unknown/ambiguous sections; replay passed.

## Files and architecture decisions

- Added `contracts/table_normalization.py` and `contracts/tables.py`: frozen
  boundary models, future callable normalizer contract, validated source/grid
  envelope, separate text records. All 13 canonical-1 storage families remain unchanged.
- Added `processing/table_grid.py`, `tables.py`, `table_corpus.py`: bounded placement,
  nested ownership, header associations, deterministic classification/rendering,
  read-only Bronze audit, replay and review-candidate generation.
- Preserved the owner's selected `processing/table_numbers.py` scaffold with
  `normalize_table_number(raw_text, *, context)` deliberately unimplemented and
  disconnected from production extraction. The practice `normalize.py` is only
  an import alias; there is one learner-owned core function.
- Added `tests/unit/test_tables.py`, `test_table_source_audit.py`,
  `test_table_numbers_assignment.py`, `tests/integration/test_table_bronze.py`,
  `tests/fixtures/tables/multi-period.htm` and `review-cases.json`.
  Concurrently supplied starter/source-audit material was preserved and validated.
- Added the `exercises` package, WP3.3 README, numeric practice tests, five starter
  cases and the reserved header-test setup. Added `docs/wp3.3-first-assignment.md`,
  `table-extraction.md`, this review, diagnostics and adjudication guide.
- Updated README, ADR-003 implementation status, data architecture, canonical
  contracts, HTML parsing, development guide and roadmap. Updated `pyproject.toml`
  only to include exercises in the source distribution and `verify-wheel.sh` to
  exercise table extraction outside the checkout. No dependency/lockfile churn.
- Preserved the pre-existing untracked WP3.2 acceptance review. No WP3.2 parser,
  section heuristic, benchmark/split/freeze or canonical storage schema was changed.

This follows ADR-003 rather than adding a store or changing architecture. It uses
the existing lxml/Pydantic dependencies, no migrations or AI libraries. Raw cells
with unsafe grids are quarantined rather than assigned invented coordinates.
Retrieval is separate from structured records; unresolved financial context stays
unknown. Symbol/spacer columns are retained instead of silently consolidating
figures. Decimal normalization is postponed only at the explicit owner boundary.

## Commands actually executed and results

Commands ran from the existing checkout using Git Bash on Windows and the locked
Python 3.12.14 / uv 0.12.23 environment.

- Initial `bash scripts/check.sh` selected the Windows WSL launcher and failed
  before checking. Retried through `C:/Program Files/Git/bin/bash.exe`.
- Baseline Git Bash `scripts/check.sh`: lock/lint/format/mypy passed; first pytest
  teardown failed on protected cache. With a writable cache: **250 passed,
  10 deselected, 0 failed/skipped/xfailed**.
- Targeted structural/integration runs passed; final focused structural run:
  **23 passed**. Strict mypy and lint/format checks passed after routine corrections.
- Final `PYTEST_ADDOPTS='-p no:cacheprovider' bash scripts/check.sh`: **278 passed,
  5 xfailed, 10 deselected; 0 failed, 0 skipped**. Lock check, Ruff lint/format and
  strict mypy passed (69 source files). Five strict xfails are exclusively the
  selected owner normalizer's `NotImplementedError`, not successful normalization.
- `bash scripts/uv.sh run --frozen python -m sec_research.processing.table_corpus
  --output .runtime/wp33/diagnostics.json`: initial all-18 structural run passed.
  Review found title-rule false positives/missed naming variants; source-linked
  synthetic regressions were added before the final diagnostic replay.
- The same command with `--output .runtime/wp33/final.json`: final all-18 audit,
  extraction, replay, JSON graph validation and table/cell source verification passed.
- Explicit practice command selecting `exercises/wp33/test_first_assignment.py`,
  `test_normalize.py` and `test_headers.py`: **29 failed intentionally at reserved
  NotImplementedError bodies** (5 starter, 23 extended numeric, 1 header). An earlier
  collection failure was fixed by adding `exercises/__init__.py`. These are outside
  the default suite and are not passing tests or pytest xfails.
- `bash scripts/verify-wheel.sh`: first attempt failed on sandbox-blocked PyPI.
  Network-enabled retry passed; final code/source-distribution rerun also passed.
  Wheel/sdist built, hash-locked runtime installation and out-of-checkout table,
  parser, contract, API and CLI smoke checks passed. Archive inspection confirms
  exercises and selected numeric scaffold are in the source distribution.
- Changing source-distribution contents triggered an editable rebuild: the
  sandbox run failed downloading `editables`; approved network retry rebuilt it.
  A cross-context pytest cache permission failure was resolved by disabling only
  pytest's optional cache provider; no assertion or warning policy was weakened.
- `bash scripts/docker.sh compose ps`: failed because Docker Engine is unavailable
  (also reported protected user Docker configuration). **Database integration and
  container build/start checks were not run**; no dedicated test URL was supplied.
- `git diff --check` passed. Diff review found no source/lockfile overwrite, secret
  additions or tracked large corpus outputs. No commit, push or hosted CI run.
- Final artifact validation checked 18 saved outputs, the 2,427 opaque plus 45
  layout-table reconciliation, 25 distinct source-hashed cases and all 55 local
  links in the new implementation/adjudication guides.

## Limitations, debt and acceptance

Satisfied for this increment: all-18 table identification regardless of section,
logical cells/spans and nested-table handling, conservative header/period labels,
source-linked canonical records, separate retrieval text, validated numeric
interfaces, deterministic replay, offline tests, distribution validation and
human-review candidate preparation. All warnings and unknown metadata are retained.

Outstanding: the owner numeric function and integration approval; owner-authored
multi-period assertions and their review; human adjudication of table structure,
classification, periods/units/footnotes and financial meaning; database integration
checks in an available dedicated test environment. WP3.3 cannot receive a complete
quality-gate pass until required implementations and tests pass.

Classification/title and header inference remain heuristics. A source-resolvable
cell can still have an incorrect semantic header. Retrieval excludes predicted
nonfinancial and quarantined grids, so misclassification can reduce retrieval
coverage; raw/structured tables remain available for correction. Currency/scale
labels are hints, especially mixed per-share units. Footnote markers are retained
without footnote-body resolution. Company CIK is present; legal name is not in the
filing Fetch contract. Full dates, numeric values, percentages, missing semantics,
XBRL concepts, CSS layout and financial interpretation are not inferred here.
Concrete review candidates include headings such as "Consolidated balance sheets
analysis" and a short cash-flow summary: the heuristic can call such disclosures
financial statements. Their predicted categories are deliberately unadjudicated;
humans must distinguish full statements from summaries before scoring or serving
those labels as authoritative.

The recovered DOM is the source-location authority, not proof of lossless malformed
HTML recovery. Corpus runs had no quarantines/nesting; those paths are supported
by synthetic tests, not diverse observed failures. Bounds are per table plus the
existing DOM limits; no measured worst-case CPU/memory SLA is established. All
filings were inspected diagnostically, so this is not a blind WP3.3 benchmark.
The existing JPMorgan section coverage and independent WP3.2 annotation limits
remain unresolved. Physical Silver/Gold publication and retrieval evaluation
remain future packages.

Next action: the owner implements only `normalize_table_number` and writes the
header exercise's main assertions. Review with progressive hints, validate the
attempt and request integration approval. The next package after accepted WP3.3
would be separately authorized WP3.4; it has not started.

Final warning occurrence counts (not semantic error rates):

- `classification_heuristic`: 2,472.
- `column_headers_unresolved`: 1,073.
- `html_recovered`: 2,472.
- `learner_normalizer_pending`: 2,472.
- `numeric_period_unresolved`: 861.
- `ragged_rows`: 261.
