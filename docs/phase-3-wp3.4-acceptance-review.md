# WP3.4 acceptance review — CONDITIONAL PASS

2026-10-22, Asia/Kuala_Lumpur. Reviewed **20a03bd6a0d76b77e3bc53fd3fcb2b3215c48139**.
The WP3.4 paths match the local `origin/main` reference. At review time, local
`main`/HEAD was the older Phase 1 commit `a7b9024`, so review used a temporary
Git archive. Local `main` was subsequently fast-forwarded to the existing remote
revision before publishing this report.
Source Git-blob hashes match the completion report; archive newline conversion
was reconciled without modifying implementation files. The acceptance review
performed no checkout, commit or push; the owner subsequently authorized publication.

**Decision:** automated acceptance passes for the documented, limited reported-fact
policy. No blocking financial correctness defect was reproduced in that scope.
Independent human financial accuracy verification remains outstanding. Use the
reviewed revision before any separately authorized WP3.5 work.

## Evidence

1. **PASS — counts, rejections, lineage and replay.** Independently counted
   **162,576** raw observations, **162,572** canonical facts and **4** retained
   rejections. JPMORGAN CHASE & CO: 54,102; Apple Inc.: 25,135; MICROSOFT CORPORATION: 32,671; AMAZON COM INC: 29,761; Alphabet Inc.: 20,907. Every raw observation and canonical value/date/accession
   was checked against its Bronze JSON pointer. All five logical hashes match the
   completion report and repeated normalization. All 28 Bronze manifests/objects
   pass integrity checks before and after the audit. The four JPMorgan
   `ffd:NrrtvMaxAggtOfferingPric` rows at USD indices 2053–2056 have end 2026-06-13
   after filed 2026-06-12; rejection preserves their raw contents.
2. **PASS — instant/duration and quarter/YTD.** Real Assets instants select;
   incompatible duration requests abstain. Real net-income pairs from the same
   accession and end date select by their distinct start dates. Exact USD readings:

- JPMORGAN CHASE & CO: quarter **21155000000** (2026-04-01 to 2026-06-30); YTD **37649000000** (2026-01-01 to 2026-06-30).
- Apple Inc.: quarter **29789000000** (2026-03-29 to 2026-06-27); YTD **101464000000** (2025-09-28 to 2026-06-27).
- MICROSOFT CORPORATION: quarter **31778000000** (2026-01-01 to 2026-03-31); YTD **97983000000** (2025-07-01 to 2026-03-31).
- AMAZON COM INC: quarter **62647000000** (2026-04-01 to 2026-06-30); YTD **92902000000** (2026-01-01 to 2026-06-30).
- Alphabet Inc.: quarter **112193000000** (2026-04-01 to 2026-06-30); YTD **174771000000** (2026-01-01 to 2026-06-30).

3. **PASS — historical cutoffs.** Each company was tested immediately before and
   on its first available filing date, then with original/latest/comparison modes.
   Before-first requests return no fact. JPMorgan 2020-12-31 assets retain
   **3386071000000**, filed 2021-02-23, and later **3384757000000**, filed 2023-02-21;
   the earlier cutoff cannot select the later observation. Candidate reordering
   preserves results. This verifies filing-date cutoffs against the stored current
   snapshot; undocumented historical API rewrites cannot be reconstructed.
4. **PASS — duplicates and later reporting.** Independent raw-key scanning found
   zero duplicate logical occurrences. Across the supported metric/period groups,
   **1896** have multiple reporting accessions and **138** have changing values.
   Alternatives and accession-level comparison outputs survive. Injecting an
   identical real observation leaves one selected value. Later values are not
   automatically called restatements.
5. **PASS within explicit scope — seven definitions/units.** Source descriptions
   match `RevenueFromContractWithCustomerExcludingAssessedTax`, `NetIncomeLoss`,
   `OperatingIncomeLoss`, `Assets`, `Liabilities`, `StockholdersEquity`, and
   `NetCashProvidedByUsedInOperatingActivities`. These mean customer-contract
   revenue excluding assessed tax; parent net income; operating income; assets;
   liabilities; parent permanent equity; and operating cash flow including
   discontinued operations. All seven accept **USD only**. EUR, shares,
   USD/shares and pure unit probes abstain. Explicit aliases do not cross concepts.
6. **PASS — all-company selection.** The 35 annual probes reproduce **31 selected,
   3 unsupported and 1 unavailable**. JPMorgan revenue/operating income and Amazon
   liabilities lack supported concepts; Alphabet's requested annual interval has
   no eligible mapped revenue observation. These remain explicit abstentions.
7. **PASS — ambiguity.** There are **0** incompatible same-accession groups in
   the tested real supported metric groups. Controlled conflicting variants of real
   facts return `ambiguous`, no selected value, and
   `conflicting_accession_observations`; the regression suite also checks
   incompatible same-day filings. Equivalent ties use the documented stable order.

## Verification and conditions

Fresh runs on the archived revision: focused WP3.4 pytest **67 passed**;
`bash scripts/check.sh` with the existing environment and `UV_NO_SYNC=1` passed
lock validation, lint, formatting, strict typing and **404 tests; 10 database tests
deselected**. A first collection attempt from the Phase 1 working directory failed
on a missing fixture; rerunning from the archived root passed. Database and wheel
checks were not rerun; the completion report's 414-test/91%-coverage results are
historical evidence, not new review results.

**Conditions/limits:** Company Facts dimensions remain unknown; default entity-scope
selection emits warnings, and verified-consolidated requests abstain. Fiscal
length diagnostics do not prove fiscal quarter/YTD classification. Revenue coverage
is deliberately narrower than universal total revenue. Broader accuracy,
comparability and historical API completeness are unverified. WP3.3 findings and
independent human adjudication remain unresolved. Automated source equality is
not independent human financial accuracy verification.

Detailed source pointers, hashes and case outputs: [acceptance diagnostics](phase-3-wp3.4-acceptance-diagnostics.json).
The original review wrote only ignored artifacts. This publication adds the review
and compact evidence under `docs/`; implementation code is unchanged. WP3.5 was
not started.
