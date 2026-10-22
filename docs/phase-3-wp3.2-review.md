# Phase 3 — WP3.2 review

Review date: 2026-10-20. Architecture: 3.1. Scope: **WP3.2 only**.

Deterministic Bronze HTML parsing, semantic blocks and form-aware section
classification are implemented. All 18 stored filings parsed, replayed and passed
source-locator checks. All 25 selected source-inspected boundary checks matched.
This is not whole-corpus section accuracy: labels cover selected items in seven
filings, were authored by Codex, and lack independent human adjudication. Two
JPMorgan quarterly filings have explicit classification coverage gaps below.
**Stop for review; WP3.3 has not started.**

## Inspection and decisions

Read AGENTS, architecture 3.1 requirements/data architecture, ADR-003, canonical
contracts/data dictionary, WP3.1 review and all three HTML fixtures, Phase 2 review,
ingestion ports/acquisition/local storage, manifest/inventory artifacts,
testing/evaluation/development guidance, roadmap and affected tests/configuration.
No prior parser or classifier was found. Existing Phase 2 and WP3.1 uncommitted
work on `main` was preserved. No worktree, branch switch, staging, commit, push,
publication or SEC acquisition was performed.

The pre-code plan defined a pure fetch/bytes parser, unchanged `canonical-1` rows,
a graph-validating result envelope, ordered content ownership, opaque financial
tables, form-aware DOM classification, frozen splits, independent source-anchor
annotations, replay/locator diagnostics and required quality/distribution checks.

Pinned lxml 6.1.3 supplies mature tolerant DOM recovery and XPath rather than a
second custom HTML parser. lxml-stubs 0.5.1 supports strict typing. Only these two
packages were added to `pyproject.toml`/`uv.lock` (44 resolved packages, previously
42). The runtime parser version includes actual lxml/libxml versions to avoid
claiming backend-independent DOM identity. Tested version:
`sec-html-1/lxml-(6, 1, 3, 0)/libxml-(2, 11, 9)/sec-sections-1`.

DOM extraction/classification remains ordinary Python without web frameworks,
LLMs, financial selection or persistence authority. Tiny heading-layout tables
are recognized; all other tables stay opaque. No financial cells or normalized
facts are produced. Diagnostic JSON is not a Silver/Gold dataset publication.
ADR-003 was updated to record the implementation; no architecture departure or
new ADR was required. There was no demonstrated need to change Phase 2 code or
WP3.1 canonical schemas.

## Files and interfaces

Created:

- `contracts/parsing.py`: frozen `html-result-1` envelope, source/ownership/range
  validators, logical serialization and structured per-input failures.
- `processing/{__init__,dom,blocks,sections,html}.py`: bounded decoding/recovery,
  stable numeric DOM locators, single-owner text traversal, placeholders,
  form/part/item classification, quality events and failure-isolating batch API.
- `processing/{benchmark,corpus}.py`: source-anchor labels, boundary scoring,
  read-only manifest/object audit, replay and locator validation, diagnostic CLI,
  per-form/company/section/split metrics and implementation/lock/input hashes.
- `tests/parsing_helpers.py`, `tests/unit/test_html_parsing.py`,
  `tests/integration/test_html_bronze.py`,
  `tests/contract/test_parsing_regression.py`: 60 new cases. The eight LocalBronze
  integration cases are offline and need no PostgreSQL marker.
- `tests/fixtures/parsing/`: split, source-anchor labels, pre-held-out freeze,
  three small attributed source-element assemblies, excerpt checksums and README.
- `docs/html-parsing.md`, this review, and
  [measured diagnostics](phase-3-wp3.2-diagnostics.json).

Modified: `pyproject.toml`, `uv.lock`, `.gitattributes` (new fixture exact-byte
rules), `scripts/verify-wheel.sh` (installed parser/CLI smoke), README, roadmap,
ADR-003, data architecture, canonical-contract guide, development guide and testing
strategy. Prior edits in these paths were retained. `canonical-1` JSON schemas and
the Phase 2 acquisition/storage/catalog implementation were not changed by WP3.2.

Full result documents are under ignored `.runtime/wp32/all-documents/`: 18 JSON
files totaling **18,543,412 bytes**. The run report is
`.runtime/wp32/all.json`; its small copy is committed-ready in `docs/`.
No raw filing corpus or full parsed corpus was added to Git.

## Current Bronze verification

The existing CLI reconciled the actual PostgreSQL catalog against stored manifests
and objects: **28 fetches, 28 objects, zero orphans**, exit 0. Independently, the
WP3.2 runner compared all immutable manifests byte-for-byte with their inventory
envelopes, read all content-addressed objects through LocalBronze, revalidated
checksums/byte counts/source metadata, and checked that manifest/object identity
sets contained no missing or extra entries. It repeated this audit after parsing.

Verified scope: **18 primary filings, five companies, eight 10-Ks, ten 10-Qs**;
the other ten objects are submissions/Company Facts responses. Parsing did not
change Bronze. These checks verify integrity and metadata lineage, not SEC
disclosure truth or financial correctness.

## Measured parsing and structural diagnostics

All 18 filings parsed with zero parse failures. All **22,453 blocks** had uniquely
resolvable DOM locators and correct normalized-text offsets. All **364 sections**
passed graph/range validation. Blocks comprise 555 headings, 19,471 paragraphs
and 2,427 opaque tables. Real-corpus list markup was not observed in emitted
blocks; nested list extraction is tested with synthetic fixtures.

There are 276 classified sections and four ambiguous missing-part sections.
**9,241 blocks** are retained in unclassified/ambiguous ranges, including covers,
TOCs, part preambles, signatures, JPMorgan annexes and quarterly unlabeled content.
No completeness claim is made for severely malformed material lost by HTML recovery.

Structural priority-section occurrence counts, without an accuracy claim:

- 10-K Item 1, Item 1A, Item 7 and Item 8: each detected in **8/8** filings.
- 10-Q Part I Item 1 and Item 2: each detected in **8/10** filings.
- 10-Q Part II Item 1A: detected in **10/10** filings.
- Other detected form/part/item counts are recorded separately under
  `structural_section:*` in the diagnostic JSON; they are not expected-label scores.

Every source was parsed twice with identical logical bytes, then its serialized
envelope was revalidated. Logical identities exclude fetch occurrences; a
separate unit test verifies that a changed fetch ID only changes provenance.
The sequential per-filing diagnostic times sum to **47.697 seconds**, including
two parses, validation and locator resolution. This is a local diagnostic
measurement under concurrent development activity, not a throughput benchmark or
worst-case latency guarantee.

## Split, source labels and boundary results

The split was fixed before heuristic development: earliest company/form filing
for development (ten); remaining newer filings held out (eight). Direct source
inspection selected 18 ranges in five development documents, covering all five
companies. Algorithm/lock hashes were then frozen before source annotation of two
preselected held-out documents (Apple 10-Q and Microsoft 10-K, seven ranges).
The frozen implementation evaluated all 18 filings once, including the eight
held-out cases. No heuristic was changed after seeing held-out results.

Expected labels are source XPath anchors and source headings, not predicted block
ordinals. Both opening and next-section anchors are checked against original
source hashes. End labels mean the block immediately before the next section
heading, including intervening running headers. Codex manually selected and
inspected these source anchors; **human adjudication is outstanding**. This is
selected agent-authored source review, not an independently human-labeled gold set.

Selected exact start-and-end matches:

- Development: **18/18** ranges in five labeled filings; ten development filings
  total received smoke/structural checks.
- Held out: **7/7** ranges in two labeled filings; eight held-out filings total
  received smoke/structural checks.
- 10-K: **16/16** labeled ranges; 10-Q: **9/9** labeled ranges.
- By company: Apple **7/7**, Microsoft **7/7**, Alphabet **3/3**, Amazon **4/4**,
  JPMorgan **4/4**. These denominators are selected labels, not filing totals.
- By section type: 10-K I:1, I:1A, II:7 and II:8 each **4/4**;
  10-Q I:1, I:2 and II:1A each **3/3**.

No whole-document precision/recall, corpus-wide section detection accuracy,
human agreement or confidence interval is claimed. Unlabeled implicit headings,
including the JPMorgan quarterly gaps, are not hidden inside a perfect score.

## Warnings, failures and limitations

There are **128 quality warnings**, with zero parse failures:

- `html_recovered`: 18; `toc_content_retained`: 18;
  `unclassified_content`: 18; `part_preamble`: 48;
  `non_item_section` (signatures): 18.
- `missing_part`: four; `missing_priority_i_1`: two;
  `missing_priority_i_2`: two.
- By form: 10-K **62 warnings / 0 failures**, 10-Q **66 / 0**.
- By company, with current filing totals: JPMorgan **24 / 0** across three;
  Apple **28 / 0** across four; Microsoft **28 / 0** across four;
  Amazon **20 / 0** across three; Alphabet **28 / 0** across four.

Recovery warnings include libxml2's recognition limits for inline-XBRL tags;
separate development-source diagnostics showed capped logs containing
`HTML_UNKNOWN_TAG`. They do not imply 18 failed documents, prove zero data loss,
or enumerate every repair. Preambles/signatures/TOCs are retained quality states,
not extraction failures.

Both JPMorgan 10-Qs (`0001628280-26-029344`, `0001628280-26-054343`) organize the
long financial/management material without the expected explicit opening item
headings. Part I Items 1/2 remain unclassified; Items 3/4 have ambiguous missing
part context. Part II items are classified. This implementation does not invent
context from a TOC or resolve incorporation-by-reference. JPMorgan's annual item
references can point to distant report material; a contiguous section range does
not resolve those references into a semantic document graph.

Other limits: only primary documents and four supported 10-K/10-Q form variants;
no exhibit traversal, financial table cells, CSS/browser layout, raw XBRL context
normalization, financial selection, chunks, Parquet publication or evidence
registry. Some narrative in layout tables intentionally remains opaque. The
heading-table heuristic and short-title recognition can miss unfamiliar layouts.
There is no separate CPU watchdog, cross-platform result comparison or adversarial
worst-case memory benchmark. The dependency lock and parser backend identity bound
reproducibility; they do not prove universal HTML recovery quality.

## Commands actually executed

Native commands used `.venv/Scripts/python.exe` (Python 3.12.14); `bash` commands
used `C:/Program Files/Git/bin/bash.exe`. Public disposable local URLs from
`docs/development.md` were used explicitly. No private contact value was recorded.

- Baseline `bash scripts/check.sh` with dedicated `sec_research_test` and
  `PYTEST_ADDOPTS='-o cache_dir=.runtime/pytest-wp32'`: lock/lint/format/type checks
  passed; **200 passed in 14.82 seconds**, zero failed/skipped/expected failures,
  93% branch-aware coverage.
- `python -m sec_research.ingestion.cli reconcile`, against the existing local
  development catalog: exit 0, 28 fetches, 28 objects, zero orphans; read-only.
- `bash scripts/uv.sh add lxml==6.1.3` and
  `bash scripts/uv.sh add --dev lxml-stubs==0.5.1`: successful locked installation
  with authorized package-registry access; no existing pins changed.
- Focused pytest runs progressed through **36**, **44**, **55**, then **59 passing**
  tests as cases were added. One new dense unlinked-TOC test initially failed
  (**1 failed, 54 passed**); the run-boundary heuristic was fixed and the assertion
  retained. The final full suite includes that test and the subsequent freeze guard.
- `python -m sec_research.processing.corpus --split development --output
  .runtime/wp32/development.json`: exit 0, 10 parsed; selected 18 boundaries matched.
  This earlier development report preceded the final warning/signature additions
  and is superseded for measurements by the final report.
- `python -m sec_research.processing.corpus --split all --output
  .runtime/wp32/all.json`: exit 0; final measurements above. Input, split,
  benchmark, implementation and lock hashes are in the report. This is the sole
  held-out parsing/scoring run for this implementation.
- Final `bash scripts/check.sh`, with dedicated `sec_research_test` and the same
  writable cache: **passed**. Locked resolution of 44 packages; Ruff lint and
  format (61 files); strict mypy (59 source files); **260 tests passed in 18.83
  seconds**, zero failed/skipped/expected failures, 92% branch-aware coverage.
  Tests created/dropped only uniquely named disposable test databases.
- `bash scripts/verify-wheel.sh`: **passed** on the network-enabled retry. Built
  wheel/sdist, hash-installed 24 locked runtime distributions plus the project in
  a temporary environment, then checked contracts, parser replay, packaged typing
  marker, API and both CLIs from outside the checkout.
- `git diff --check`: passed. Final hash verification confirmed that the recorded
  implementation, lock, split and label hashes still match, that the pre-held-out
  algorithm freeze is intact, and that all 18 full result artifacts exist.
  Reviewed dependency changes, UTF-8 output, ignored corpus outputs and changed-file
  scope; no source data, credentials or unrelated application edits were added.

Initial default pytest cache writes failed with a permissions warning after test
execution; the writable `.runtime` cache resolved this without weakening warning
policy. Direct uv initially hit its protected default cache; the existing wrapper
resolved that. Sandbox package downloads/build isolation initially failed with
socket-denied errors; authorized retries passed with TLS/pins/hashes preserved.
An exploratory output write used Windows' default encoding and failed; diagnostic
files now use explicit UTF-8. Intermediate formatting/type errors were corrected,
including the resolver stub/runtime signature difference. No such issue remains
in the final required checks.

Container build/start, hosted CI, shared deployment, live SEC reacquisition,
model/RAG evaluation, human label adjudication and financial correctness checks
were **unrun** and are not claimed. They are not implemented by this package.

## Acceptance and next gate

Satisfied: deterministic tolerant parsing; ordered validated blocks; opaque table
references; form-aware explicit heading classification; preservation of ambiguous
and unclassified content; complete validated provenance links and reading-order
ranges; all-18 real replay/locator/manifest checks; frozen split; documented
source-inspected selected labels; automated unit/integration/regression cases;
full required quality and distribution checks; updated guidance and roadmap.

Outstanding for broader quality claims: independent human adjudication, broader
expected-boundary labels and JPMorgan quarterly implicit-section coverage. These
are visible review decisions and technical debt, not passing accuracy criteria.
No requirement for universal detection or a numeric section-accuracy threshold
was supplied; this review does not invent one or conceal the observed gaps.

Review these results and limits before authorizing **WP3.3 structured table
extraction**, using existing table placeholders/locators. No WP3.3 implementation
or additional heuristic tuning has started.
