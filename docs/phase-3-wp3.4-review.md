# WP3.4 XBRL financial fact normalization review

Review date: 2026-10-22, Asia/Kuala_Lumpur. Architecture 3.1 / ADR-003 / ADR-006.
Branch retained: `feat/sec-ingestion-html-parsing`. No commit or push.
The corpus selection cutoff is intentionally pinned to **2026-10-21**.

## Scope and decision

WP3.4 implements deterministic Company Facts normalization and a narrow reported
metric selector. The owner explicitly authorized this package while deferring
independent WP3.3 financial adjudication. That adjudication is **not passed**;
WP33-REV-001 through -006 and JPMorgan's section-classification limitations remain
unresolved. No WP3.2/WP3.3 behavior was changed, and no HTML values replace facts.

Final verification results are recorded below. Financial selection accuracy is
not claimed: the examples are source-linked regression evidence, not independent
ground truth. WP3.5 remains unstarted and requires explicit authorization.

## Changes and architecture decisions

New implementation:

- `contracts/xbrl.py`: versioned occurrence, concept, rejection, request and
  selection envelopes with source-graph validation.
- `domain/periods.py`, `domain/metrics.py`, `domain/financial_selection.py`, and
  `domain/__init__.py`: date diagnostics, seven exact concept mappings, explicit
  aliases, eligibility, original/latest/comparison modes and ambiguity handling.
- `processing/xbrl.py`: checksum-verified Company Facts parser; numeric lexemes
  become Decimal without float conversion; raw accepted/rejected observations
  survive with pointers, source/fiscal metadata and stable identities.
- `processing/xbrl_corpus.py`: read-only Bronze audit, replay, source resolution,
  round trip, source-linked examples and 35 annual selection probes.
- `tests/xbrl_helpers.py`, `tests/unit/test_xbrl.py`,
  `tests/unit/test_financial_selection.py`, `tests/unit/test_xbrl_examples.py`,
  `tests/integration/test_xbrl_bronze.py`, and `tests/fixtures/xbrl/`: synthetic
  edge cases, real examples and offline LocalBronze/CLI integration.

Modified: `contracts/canonical.py` and `docs/schemas/canonical-1.json` add the
`company_facts_entity` metric-context option; canonical financial rows and existing
identities remain unchanged. Old catalog readers must update before accepting the
new option. `scripts/verify-wheel.sh` now exercises the installed normalizer,
selector and audit CLI. No new dependencies, lockfile changes, database migrations,
distributed infrastructure or framework-bound domain logic were introduced.

Documentation: added `docs/xbrl-normalization.md`, this review, and the small
`docs/phase-3-wp3.4-diagnostics.json` report; updated ADR-003, ADR-006, canonical
contracts, data architecture, development instructions, roadmap, README and
AGENTS.md. All pre-existing uncommitted WP3.3 implementation, review material and
exercises were preserved. Large envelopes remain ignored under `.runtime/wp34/`.

The material ADR-006 refinement permits the documented Company Facts entity scope
for these reported metrics with a warning, while retaining a stricter
`verified_consolidated` request that abstains on unknown contexts. Dimensions and
context IDs stay unknown. Requiring verified contexts universally would prevent
Company Facts-only selection. Arbitrary concept aliasing and implicit dimensional
verification were rejected. Period length is diagnostic only: exact dates govern
selection, and duration classifications remain unknown without fiscal anchors.

## Corpus results

Five existing artifacts contain **162,576 source observations**. Normalization
produces **162,572 canonical financial facts** with retained context warnings and
**4 rejected raw occurrences**. Counts include all taxonomies, units and forms;
normalizing an observation does not make it eligible for the small metric catalog.

- JPMorgan: **54,102** observations; `us-gaap` 49,845, `ffd` 4,033, `dei` 101,
  `invest` 70, `ecd` 35, `srt` 18. 54,098 warning facts and four rejected occurrences.
- Apple: **25,135**; `us-gaap` 25,046 and `dei` 89. All retained with warnings.
- Microsoft: **32,671**; `us-gaap` 32,536 and `dei` 135. All retained with warnings.
- Amazon: **29,761**; `us-gaap` 29,636, `dei` 87, `ffd` 23, `ecd` 15.
  All retained with warnings.
- Alphabet: **20,907**; `us-gaap` 20,808, `ffd` 52, `ecd` 35, `dei` 12.
  All retained with warnings.

Aggregate taxonomy counts: `us-gaap` **157,871**, `ffd` **4,108**, `dei` **424**,
`ecd` **85**, `invest` **70**, `srt` **18**.

Valid period diagnostics: **67,848 instants**, **35,317 quarter-length**,
**13,395 half-year-length**, **12,869 nine-month-length**, **33,069 annual-length**,
and **74 other durations**. Half/nine-month lengths are not asserted to be YTD;
quarter/annual lengths are not asserted fiscal classifications. Synthetic tests
cover exact YTD/quarter selection, historical comparatives, leap years and
52/53-week intervals independently of `fy`/`fp` and filing dates.

Warnings overlap: **156,420** retained observations use concepts outside the seven
metric mappings; **9,680** have unsupported filing forms; **5,946** lack optional
fiscal metadata; **188** have units outside the recognized normalization unit set.
All **162,572** canonical observations retain unknown-context warnings. There are
**zero logical duplicate-observation warnings** in these five artifacts; duplicate
preservation/deduplication is separately tested with synthetic inputs.

The four rejections are JPMorgan `ffd:NrrtvMaxAggtOfferingPric`, USD array indices
2053–2056, accessions `0001213900-26-068092`, `0001213900-26-068158`,
`0001213900-26-068360`, and `0001213900-26-068361`. Each reports end `2026-06-13`
with filed `2026-06-12`, form `424B2`. This violates the canonical observation
availability invariant. Their complete raw JSON remains retained; they are not
supported financial metrics. No claim that the SEC source is corrupt is implied.

## Selection and evaluation evidence

Supported metrics: customer-contract revenue excluding assessed tax, parent net
income, operating income, total assets, total liabilities, parent permanent
stockholders' equity, and operating cash flow including discontinued operations.
The [guide](xbrl-normalization.md) records exact concepts, aliases and limitations.
No broader revenue, ProfitLoss, consolidated equity including noncontrolling
interests, or calculated liabilities substitution occurs.

The **35 annual diagnostic probes** produce **31 selected**, **3 unsupported**,
**1 unavailable**, and **0 ambiguous** results. JPMorgan revenue and operating
income have no supported concept; Amazon total liabilities has no supported
concept. Alphabet's supported customer-contract revenue concept has no eligible
observation for the requested annual interval. These are explicit abstentions,
not inferred values. Zero ambiguity describes only these 35 probes, not every
possible request; synthetic incompatible-accession and same-day conflicts abstain.

The **15 source-linked regression examples** include the following 2025 annual
source readings (USD, unscaled): Apple net income **112010000000**, Microsoft net
income **101832000000**, Alphabet net income **132170000000**, Amazon operating
cash flow **139514000000**, and JPMorgan operating cash flow **-147782000000**.
The fixture retains each source hash, pointer, accession and interval; the
independent-review fields remain null. Microsoft and Apple have non-calendar
fiscal boundaries. Values here establish source preservation only, not financial
adjudication or an accuracy score.

Selection requires exact CIK/concept/actual interval/kind/unit and cutoff, supports
original/latest-as-of/compare-versions, retains accession-level alternatives, and
returns eligibility explanations. It does not select merely the newest Company
Facts row. Same-accession incompatible reportings and incompatible same-day
finalists remain ambiguous. Equivalent ties use accession then record ID.

## Provenance and reproducibility

All **28 Bronze fetches/objects/manifests** are audited before and after the run;
all five Company Facts checksums and lengths are verified. **162,576 observation
pointers**, concept metadata pointers and all **15 regression-example pointers**
resolve to their original source. Each artifact is normalized twice with identical
logical bytes and passes envelope serialization/revalidation. Raw occurrence
values, intervals, accession, form, availability, units and fiscal fields are
checked against canonical rows. Bronze is unchanged; no SEC requests were made.

The [diagnostic summary](phase-3-wp3.4-diagnostics.json) records code hashes, source hashes, logical and
output hashes, policy versions, lock hash, and a deterministic input-dataset hash.
It is a diagnostic snapshot, not an activated Silver/Gold dataset or a Parquet
manifest. Full envelopes reside in `.runtime/wp34/diagnostics-observations/`.

## Commands and verification

- Baseline `bash scripts/check.sh`: locked dependencies, lint, format and strict
  typing passed; **337 passed, 10 deselected** offline tests.
- Focused WP3.4 suite before the final envelope checks: **62 passed**.
- Full `bash scripts/check.sh` with the documented local `sec_research_test`
  connection: an intermediate run passed **409 tests**, zero failed/skipped/xfail,
  **91% branch-aware coverage**, 16.31 seconds. The final run is recorded below.
- `python -m sec_research.processing.xbrl_corpus --as-of 2026-10-21 --examples
  tests/fixtures/xbrl/reported-examples.json --output .runtime/wp34/diagnostics.json`:
  all-five normalization, replay, pointer and immutable Bronze checks passed.
- `bash scripts/verify-wheel.sh`: passed on the network-enabled retry, installing
  24 locked hash-verified runtime packages plus the wheel in a clean temporary
  environment and exercising normalization/selection/CLIs outside the checkout.
  Final post-validation-change run is recorded below.

Final checks:

- `bash scripts/check.sh` with `TEST_DATABASE_URL` set to the dedicated
  `sec_research_test`: **414 passed**, **0 failed/errors/skipped/xfail** in
  **18.47 seconds**. Lock validation, Ruff lint, formatting (88 files) and strict
  mypy (83 files) passed. Integration fixtures used uniquely named disposable
  databases; no user/production database was migrated or dropped.
- **91%** overall branch-aware coverage; financial selection, metric catalog and
  period diagnostics **100%** each; normalizer **93%**, envelope **84%**, offline
  audit command **75%**. Real-corpus execution is separate from test coverage.
- Final offline run: **404 passed, 10 deselected**, 11.09 seconds.
- Final `bash scripts/verify-wheel.sh`: **passed**, including the final
  source-pointer validators, installed normalizer/selector and CLI smoke checks.
- `git diff --check`: **passed**. Dependency lock unchanged; runtime envelopes and
  wheel outputs remain ignored. Existing unrelated working changes were preserved.
- Final artifact audit: current code/lock hashes and all five output checksums
  match the report; **280,147,247 bytes** of full envelopes remain ignored. New
  documentation links/fences pass. Distribution inventory checks found **54 wheel**
  and **189 source-archive entries**, including the new modules and small fixtures,
  excluding runtime data and private environment files. The final review text and
  diagnostic-summary copy were completed after this distribution build; verified
  application code is unchanged.

Diagnosed intermediate issues: one synthetic test supplied a string UUID through
validation-bypassing `model_copy`; corrected to an actual UUID. Real SEC concepts
had blank labels/descriptions, now preserved and regression-tested. Ruff formatting
and a local variable typing collision were corrected. Initial database checks
could not connect because the existing Compose service was stopped; started that
service, then passed the full isolated database suite. The initial waiting run was
interrupted, not counted as passing. After the session resumed, Docker Desktop was
also stopped: that attempted full run ended with **411 passed, 3 database setup
errors** in 286.56 seconds. Restarted Docker Desktop in the background and brought
up the existing Compose database; the final clean run above passed all 414 tests.
Initial wheel resolution was blocked by the network sandbox; the authorized retry
retained pins, TLS and hash verification. No assertions were weakened.

Hosted CI, live SEC reacquisition, shared deployment, container rebuild, independent
financial adjudication, exhaustive all-period selection evaluation, performance
SLA measurement and WP3.5 publication checks were not run and are not claimed.

## Acceptance and next gate

The bounded engineering criteria are met with the recorded closing checks:
all five artifacts are processed; exact canonical observations and period/fiscal
metadata survive; source lineage and replay are verified; selection is deterministic
and explainable; incompatible cases abstain; automated regression and installed
distribution checks exercise the implementation. Limitations and rejected raw
observations remain visible.

Outstanding quality work: independent financial labels/selection adjudication,
broader catalog coverage, full XBRL context/taxonomy-version evidence, fiscal
calendar-backed classification, historical API completeness, intraday availability,
and the deferred WP3.3 structural/financial findings. No financial accuracy claim,
formula calculation, Q4 derivation or cross-source reconciliation is made.

WP3.5 can be planned around these versioned contracts and quality states, with
explicit policy for quarantined rows and warnings. It is **not implemented or
authorized**. Stop for this package's review before starting physical dataset
publication. Preserve the owner-deferred adjudication items in later gates.
