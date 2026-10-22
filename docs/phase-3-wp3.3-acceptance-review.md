# WP3.3 completion and acceptance review

Review date: 2026-10-21, Asia/Kuala_Lumpur. Architecture 3.1 / ADR-003.
Branch retained: `feat/sec-ingestion-html-parsing`. No commit or push.

## Decision

The previously reserved implementation is complete: numeric normalization,
validation, multi-period header tests, and extraction integration. Hands-on
assignments are paused; Codex owns implementation and maintenance. Existing
practice tests remain executable and the import alias points to one production
normalizer. No working implementation or unrelated files were deleted.

Engineering verification passes. Final financial acceptance remains open for
independent source adjudication and owner review. Passing unit tests, deterministic
replay, and source preservation do not establish extraction accuracy. WP3.4 has
not started and is not authorized by this report.

Subsequent [human review](phase-3-wp3.3-human-review.md) has started: the user
supplied seven source readings for the first JPMorgan table, matching the retained
heading/years and five selected amounts with their row/year links, including an
accounting negative. This is partial
review; no table or corpus financial acceptance has been recorded. For candidate 2,
the user also supplied matching 2025/2024 total-assets readings and confirmed
headings after Codex supplied their wording. Both table reviews remain partial.
The user's subsequent `11 %` reading confirmed **WP33-REV-001**: candidate 2's
total-assets change preserves separate number/symbol cells but leaves the number's
percentage flag false. This unresolved financial-context limitation is recorded
in the human review log; no repair or financial acceptance is claimed.
The user also confirmed candidate 2's `Selected Consolidated balance sheets data`
caption. **WP33-REV-002** records a source-supported classification concern:
Codex proposes `financial_disclosure` for this selected asset-analysis table,
currently labeled `financial_statement`; human category disposition remains pending.
The user subsequently confirmed, with a screenshot and an explicit reading, that
this table ends at `Total assets`. Its selected-data caption and extent are now
human-confirmed; the category correction is still Codex's assessment. Both recorded
findings remain unresolved, and candidate 2 has not been accepted.
For candidate 3, the user's 2025 net-income and operating cash-flow readings match
the extracted amounts and row/year links, including the parenthesized negative.
This cash-flow table review is partial; no table or corpus acceptance is implied.
The candidate 3 Visa-row reading (—, (7,990), —) confirmed the tokens behind
**WP33-REV-003**. For candidate 4 (Q1 2026 10-Q), five unprompted readings
matched; they show `%` only on the first and total rows, extending WP33-REV-001
to a column-level unit convention, and WP33-REV-002 recurs. Candidate 5 (Q2 2026
10-Q): five unprompted readings matched; the user observed `$` likewise only on
first/total rows (existing currency limitation). Candidate 6 (Apple Q2 FY2026
operations): six readings matched; they confirmed **WP33-REV-004** (label-only
group rows unlinked, so duplicated `Products`/`Basic` labels are ambiguous) and
**WP33-REV-005** (units line outside the table not captured; group labels
recorded as unit hints). Candidate 7 (Apple balance sheet): six readings matched; REV-004 (current vs non-current `Term debt`) and REV-005 recur; balance identity holds. Candidate 8 (Apple cash flows): six readings matched; REV-004 (three `Other` rows) and REV-005 recur; cash reconciliation and cross-table balances hold. Candidate 9 (Apple comprehensive income): readings matched (one requested derivative-row value not yet supplied); REV-004 and REV-005 recur; totals reconcile. Partial review only.

Candidates 10 and 11 received assisted checks of selected displayed values.
The user chose to stop the repetitive candidate walk and prioritize review of
the confirmed defects. A targeted recheck of WP33-REV-001 through -005 against
the current extractor and source-linked records found them unresolved. Candidate
11 exposed **WP33-REV-006**: its 2025 and 2024 `Other income (expense), net`
negatives have parentheses split across cells. The displayed entries are
correct, but the structured number cells are `uncertain` with null values;
candidate 12 contains the same pattern in an unreviewed row. No fix or
independent corpus accuracy result is claimed.

## Implementation and contracts

- `processing/table_numbers.py`: exact displayed Decimal parsing, ASCII signs,
  accounting negatives, comma grouping, percentages, zero/missing distinction,
  and conservative abstention. Raw text and supplied context are preserved.
  Large negatives do not pass through context-sensitive Decimal arithmetic.
- `contracts/table_normalization.py`: validated result states, finite exact values,
  consistent flags, and the canonical status mapping. Nonblank missing dashes
  remain canonical `uncertain` while their context records `missing`.
- `processing/tables.py` and `contracts/tables.py`: integrated results and
  cell/context agreement, numeric-footnote abstention, unchanged source/header
  ownership, and separate retrieval text. Units, scale, and currency remain unknown
  in extraction because raw hints can mix units. No filing-date period inference.
- `processing/table_corpus.py`: per-filing and aggregate normalization counts,
  source checks, deterministic replay, and versioned diagnostics.
- `tests/unit/test_table_numbers.py`, `test_table_headers.py`,
  `test_table_numbers_assignment.py`, and `test_tables.py`: edge cases,
  contradictory-state rejection, numeric-footnote handling, merged headers,
  duplicate-text header identities, duration/year separation, and a cell spanning
  incompatible period columns. Strict learner xfails were removed.
- `tests/integration/test_table_bronze.py` and `scripts/verify-wheel.sh`:
  integrated numeric assertions in the offline Bronze path and installed package.
- `AGENTS.md`, README, ADR-003, architecture/contracts/development/roadmap/table
  guides, and exercise instructions now describe Codex-led development. The old
  assignment and structural review remain explicitly historical.

Versions are `table-numeric-1`, `sec-tables-2`, `table-result-2`, and `table-text-2`.
The result schema change rejects historical pending scaffolds; earlier outputs
remain historical artifacts, rather than silently acquiring new semantics.
Canonical-1 storage families, WP3.2 parsing/section heuristics, dependencies, and
the lockfile are unchanged by this completion. IDs change with processing versions;
source bytes and document provenance do not.

This implements ADR-003 without a new architecture or store. Alternatives rejected:
duplicating the exercise normalizer, guessing currency/scale, stripping footnotes
to manufacture values, and treating lexical numbers as selected financial facts.
No Spark, Delta, AI framework, publication, or WP3.4 code was added.

## Commands executed

Commands ran from the repository root, using Python 3.12.14 and the locked uv
0.12.23 environment. Shell scripts used `C:/Program Files/Git/bin/bash.exe`.
`PYTEST_ADDOPTS='-p no:cacheprovider'` avoided the protected historical cache;
`UV_OFFLINE=true` used cached, hash-verified artifacts without changing TLS policy.

- Focused numeric/header/structure plus exercise pytest run: **111 passed**.
- `bash scripts/check.sh` without a database: **337 passed, 10 deselected**;
  locked dependencies, Ruff lint/format, and strict mypy passed.
- Started a dedicated `--rm` PostgreSQL test container from the repository's
  digest-pinned pgvector image, bound to `127.0.0.1:55433`, database
  `sec_research_test`. No existing application database was used or migrated.
- `bash scripts/check.sh` with `TEST_DATABASE_URL` pointing to that isolated
  database: **347 passed, 0 failed, 0 skipped, 0 xfailed, 0 deselected**.
  Includes all ten PostgreSQL tests; fixtures created/dropped uniquely named
  databases. Lock validation, lint, format, strict typing passed (71 source files).
  Overall measured test coverage: 91%; coverage is not financial accuracy.
  The disposable container was stopped after the tests and removed by `--rm`.
- `python -m pytest exercises -p no:cacheprovider -q`: **29 passed**.
  Explicit Ruff and strict mypy checks on the preserved exercises also passed.
- `bash scripts/verify-wheel.sh`: **passed** wheel/sdist build, hash-locked install,
  and out-of-checkout contract/parser/table/API/CLI smoke checks, including Decimal
  integration. No database is needed for this distribution check.
- `python .runtime/wp33/finalize_completion.py`: passed artifact/hash/count checks
  and generated the current compact candidate manifest and completion summary.
- Local Markdown link check: 129 existing targets verified.
- `git diff --check`: passed after removing a trailing blank line in AGENTS.md.

Initial checks found formatting/Unicode-literal lint issues and a nullable cell-ID
typing issue in new tests; these were corrected without weakening assertions.
The first Docker check was sandbox-denied; the approved outside-sandbox check
succeeded, allowing the complete database suite. There are no remaining failed
automated checks. Hosted CI, full application container build/start, live SEC
downloads, and human adjudication were not run in this completion.

## Corpus validation

`bash scripts/uv.sh run --frozen python -m sec_research.processing.table_corpus
--output .runtime/wp33/completion.json` completed successfully. The
[current diagnostics](phase-3-wp3.3-completion-diagnostics.json) record code, lock,
inventory and source hashes, per-filing counts, and logical output hashes.

- **18/18 filings**, five companies, eight 10-Ks and ten 10-Qs: extraction,
  deterministic replay, validated JSON round-trips, and source audit passed.
- **2,472 tables / 300,260 source cells** verified; no extraction failures or
  quarantines. All prior structural counts and all source hashes match the earlier
  structural run. There are 89 predicted statements and 1,122 predicted disclosures;
  these remain heuristic categories, not measured classification accuracy.
- **28 Bronze fetches / 28 objects** audited before and after; unchanged.
- Lexical results: **52,604 parsed**, **198,572 missing**,
  **40,178 not_numeric**, **8,906 uncertain**,
  **0 pending**. Counts include all reconstructed cells, including blank/spacer
  and header cells; they are not counts of verified financial observations.
- Numeric uncertainty warnings: `{'unsupported_numeric_format': 8513, 'footnote_numeric_ambiguity': 393}`. Abstentions are retained,
  not silently removed from denominators or converted to zero.
- Both JPMorgan quarters retain **270 / 279 tables**, **39,082 / 52,678 cells**,
  and **267 / 276 unknown-or-ambiguous-section tables** respectively. Source
  checks and replay pass without changing their section classifications.
- [25 current review candidates](phase-3-wp3.3-completion-candidates.json), five per
  company, point to the v2 table IDs and preserved sources. All expected judgments
  remain null. The original v1 diagnostics/candidates are retained as history.

Full outputs remain ignored in `.runtime/wp33/completion-documents`. A post-run
artifact check verified all 18 result envelopes, totals, current code/lock hashes,
unchanged structural/source metrics, and resolution of all 25 candidate IDs.
No financial accuracy score is inferred from these checks.

## Remaining defects and limits

- **WP33-REV-001 (confirmed in human review):** candidate 2's total-assets change
  is displayed as `11 %` across adjacent source cells. The extractor retains both
  cells but normalizes `11` with `percentage=false`. Source-linked percent context
  association or explicit unresolved-unit abstention is required before this entry
  can be accepted as a correctly interpreted financial value. Automated checks
  remain passing; they do not currently enforce this cross-cell interpretation.

- **WP33-REV-003 (source tokens confirmed by user):** a leading en/em
  dash before a row's first amount is marked as a row header. Corpus-wide: 800
  dash headers, 135 tables, 17/18 filings, 6,232 cells with a spurious header
  link. See the [human review log](phase-3-wp3.3-human-review.md).

- **WP33-REV-002, -004, -005 (source-supported, unresolved):** selected
  balance-sheet analysis is labeled a full statement; label-only group rows
  fail to distinguish repeated leaf labels; and adjacent units paragraphs can
  be absent from table hints while group labels appear as unit hints.

- **WP33-REV-006 (source-linked, unresolved):** separate closing-parenthesis
  cells leave candidate 11's visually negative other-income amounts without
  parsed numeric values. The single-cell normalizer abstains as designed; a
  future context policy requires source-linked pairing or explicit abstention.

- Independent structural and financial labels remain unadjudicated. Source-linked
  candidates are predictions, with null expected judgments; no accuracy, precision,
  recall, or human agreement is claimed. The diagnostic corpus is not a blind
  benchmark and does not replace the frozen WP3.2 evaluation protocol.
- Both JPMorgan 10-Qs retain the Part I Items 1/2 section-classification limitation.
  Tables remain extractable in those unknown/ambiguous sections; this package does
  not relabel them.
- The table classifier can label summaries or "balance sheets analysis" as full
  statements. Misclassification can exclude tables from retrieval, although raw
  and structured results remain available. No independently measured error rate.
- Header links and period labels are structural hypotheses. Full date intervals,
  quarter-versus-YTD meaning, financial concept mapping, dimensional context,
  footnote bodies, and mixed-unit application remain unresolved.
- Lone dashes use the bounded missing policy; real statements can use dashes for
  zero. Currency symbols, Unicode minus, locale/scientific formats, and attached
  numeric footnotes abstain. Separate symbol/sign/percent cells are not combined;
  a parsed token is not an asserted financial amount with resolved context.
- HTML recovery, CSS visibility/layout, malformed grids, nested tables, and resource
  bounds have existing limits. Synthetic failure-path tests do not prove robustness
  against all filings, and there is no measured worst-case resource SLA.

## Acceptance and next package

Satisfied: Codex-led instructions; preserved exercises; one integrated normalizer;
deterministic Decimal behavior; validation and multi-period regressions; complete
test/quality/distribution checks; all-18 corpus replay/source audit; versioned outputs
and unchanged source authority.
Independent financial acceptance and owner package review remain outstanding.

Next recommended action is review and adjudication of WP3.3. WP3.4 XBRL concept
mapping is the next implementation package only after that review and explicit
authorization. It has not been started.
