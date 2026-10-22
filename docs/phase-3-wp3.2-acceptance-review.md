# WP3.2 — Independent Engineering Acceptance Review

Review date: **2026-10-20** (user context, Asia/Kuala_Lumpur). Architecture **3.1**. Reviewed checkout **`bafa838`**. Scope: read-only implementation review of SEC HTML parsing and section extraction; only this report is added to tracked files.

## Recommendation

**CONDITIONAL PASS — Proceed with documented limitations.** WP3.2 provides a reproducible, source-linked substrate for WP3.3 structured table extraction. Both JPMorgan 10-Qs retain their financial and MD&A material, including all independently enumerated visible top-level tables, but lack classified Part I Items 1/2. WP3.3 must accept tables from unclassified/ambiguous ranges and preserve unknown section metadata. These gaps are a material blocker to claiming complete section-filtered retrieval, not to beginning bounded table extraction. Human adjudication of boundary labels remains outstanding. No WP3.3 work is authorized or started by this report.

## Evidence, method and limits

Read [AGENTS](../AGENTS.md), [ADR-003](adr/ADR-003-data-pipeline.md), [completion report](phase-3-wp3.2-review.md), [HTML parsing contracts](html-parsing.md), [requirements](requirements.md), [data architecture](architecture/data-architecture.md), [WP3.1 review](phase-3-wp3.1-review.md), [roadmap](roadmap.md), and development/testing/evaluation guidance. Inspected implementation, canonical envelope validation, benchmark scoring, frozen fixtures, test configuration and clean initial Git status. No architecture or implementation change was made. The existing lxml backend and numeric DOM locator contract are reused; no alternative parser or financial interpretation is introduced.

Reran the existing corpus command against immutable local Bronze and wrote fresh diagnostics. A separate review script independently asserted source SHA-256/length/metadata consistency, direct XPath uniqueness, normalized offsets, text hashes, contiguous range ownership, stable IDs/order/ranges, exact logical hashes and source-anchor boundary equality. It used the documented parser to recover the DOM, so this is a separate engineering verification, not an independent HTML-engine comparison. It additionally enumerated all visible top-level source tables in both JPMorgan quarters. There were no SEC reacquisitions or changes to labels, splits, freeze files, parser, tests or lockfile.

**No human has reviewed these new samples or adjudicated the existing labels in this session.** Agent source inspection and passing assertions are explicitly distinct from independent human judgments. Source existence and structural validity do not establish semantic completeness, financial correctness or retrieval quality. The corpus contains five issuers, eight 10-Ks and ten 10-Qs; it is a bounded diagnostic set.

## Verified results

| Check | Fresh result | Meaning |
| --- | --- | --- |
| Primary filings parsed | 18/18; 0 parse failures | Successful parser execution, not section accuracy. |
| Immutable Bronze audit | 28 fetches, 28 objects, 0 orphans; unchanged after parsing | Inventory/manifests, checksums and byte counts validated before/after the run. |
| Source locators | 22,453/22,453 resolve uniquely; text offsets/hash checks pass | Locations address the recovered original-source DOM and normalized document text. |
| Section graph | 364/364 partition ranges validated | 276 classified, 4 ambiguous, 84 unclassified; no missing or multiply owned emitted blocks. |
| Block kinds | 555 headings; 19,471 paragraphs; 2,427 opaque tables | Opaque tables retain HTML locations; cells are outside WP3.2. |
| Selected exact source boundaries | 25/25 start-and-end ranges match frozen source anchors | 18 development and 7 held-out labels; source-authored by Codex, human adjudication pending. |
| Held-out checks unchanged | 7/7 exact; identical source/label/split/freeze hashes and outputs | These seven labels cover two of eight held-out filings; all eight receive structural smoke checks. |
| Determinism | 18/18 replay identically; 18/18 prior logical hashes unchanged | Stable document/block/section IDs, order and ranges checked explicitly. |
| Warnings | 128 quality warnings; 0 parse failures | Warnings remain unchanged; details below. |
| Full quality gate | 260 passed; 0 failed/skipped/xfailed; lint/format/type/lock pass | Automated test results, separate from source extraction measurements. |
| Distribution validation | Passed on network-enabled retry | Wheel/sdist built; hash-locked clean install and out-of-checkout smoke passed. |

Priority structural occurrence counts remain: 10-K I:1, I:1A, II:7, II:8 each **8/8**; 10-Q I:1 and I:2 each **8/10**; 10-Q II:1A **10/10**. These measure detected labels, not independently measured recall. No whole-corpus precision/recall, accuracy percentage, confidence interval, zero-loss guarantee or human agreement is established.

Warning reasons: `html_recovered` 18; `toc_content_retained` 18; `unclassified_content` 18; `part_preamble` 48; `non_item_section` 18; `missing_part` 4; `missing_priority_i_1` 2; `missing_priority_i_2` 2. Recovery warnings include inline-XBRL tag handling; capped recovery logs cannot establish the absence of lost malformed content.

## JPMorgan investigation

Both filings place their Part I item labels in TOC tables rather than explicit standalone body item boundaries. The body begins its management discussion under an `INTRODUCTION` display heading inside an opaque layout table (block 36 in Q1; block 38 in Q2), followed by ordinary MD&A prose (blocks 37 and 39 respectively). Later financial statement headings are paragraphs without `Item 1` prefixes. The TOC Part I label never establishes active body part context. The classifier deliberately skips tables/navigation, requires an explicit item prefix, and requires Part I/II context for quarterly items. Consequently it cannot infer I:1/I:2; explicit Items 3/4 remain ambiguous (`missing_part`). This is consistent conservative behavior with incomplete semantic coverage.

The order also matters: MD&A precedes the financial statements. A simple forward contiguous Item 1 → Item 2 rule would misrepresent this source. A future solution should distinguish physical ranges from semantic item membership and handle TOC references/anchors with validation, rather than trusting navigation text as a body heading or relabeling an entire range.

### 0001628280-26-029344 — 2026-03-31

[Original SEC HTML](https://www.sec.gov/Archives/edgar/data/19617/000162828026029344/jpm-20260331.htm); [exact local Bronze](../.runtime/artifacts/bronze/sha256/19/19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc). Initial unclassified range: **0–2233**, 2,234 blocks (1,961 paragraphs, 264 tables, 9 headings). This range includes cover/TOC, MD&A, financial statements/notes and later supplementary material; it is not a clean semantic Item 1/2 range.

Relevant body locations (key samples include full IDs below; the separate audit records every heading ID):

- Block **36**: opaque introduction-heading table, `/*[1]/*[2]/*[51]/*[1]`. Source text: “INTRODUCTION”.
- Block **37**: preserved MD&A narrative, `/*[1]/*[2]/*[53]/*[1]/*[1]`.
- Block **1023** (paragraph): “Consolidated statements of income (unaudited)”; `/*[1]/*[2]/*[607]`; owner: unclassified; Part unknown, Item none.
- Block **1028** (paragraph): “Consolidated statements of comprehensive income (unaudited)”; `/*[1]/*[2]/*[615]`; owner: unclassified; Part unknown, Item none.
- Block **1033** (paragraph): “Consolidated balance sheets (unaudited)”; `/*[1]/*[2]/*[624]`; owner: unclassified; Part unknown, Item none.
- Block **1040** (paragraph): “Consolidated statements of changes in stockholders’ equity (unaudited)”; `/*[1]/*[2]/*[634]`; owner: unclassified; Part unknown, Item none.
- Block **1045** (paragraph): “Consolidated statements of cash flows (unaudited)”; `/*[1]/*[2]/*[642]`; owner: unclassified; Part unknown, Item none.
- Block **1052** (paragraph): “NOTES TO CONSOLIDATED FINANCIAL STATEMENTS (unaudited)”; `/*[1]/*[2]/*[654]`; owner: unclassified; Part unknown, Item none.
- Block **2234** (paragraph): “Item 3. Quantitative and Qualitative Disclosures About Market Risk.”; `/*[1]/*[2]/*[1135]/*[1]/*[1]`; owner: ambiguous; Part unknown, Item 3.
- Block **2236** (paragraph): “Item 4. Controls and Procedures.”; `/*[1]/*[2]/*[1135]/*[1]/*[4]`; owner: ambiguous; Part unknown, Item 4.
- Block **2239** (heading): “Part II – Other Information”; `/*[1]/*[2]/*[1135]/*[1]/*[8]`; owner: unclassified; Part II, Item none.
- Block **2255** (paragraph): “Item 3. Defaults Upon Senior Securities.”; `/*[1]/*[2]/*[1144]`; owner: classified; Part II, Item 3.
- Block **2257** (paragraph): “Item 4. Mine Safety Disclosures.”; `/*[1]/*[2]/*[1147]`; owner: classified; Part II, Item 4.

Table preservation check: **270/270** visible top-level source-table locations have an emitted source owner; **270** are opaque table blocks. Nested tables remain inside their retained outer HTML table. This proves locator-level table preservation on these sources, not complete financial-cell interpretation.

TOC source labels/links (navigation only; not accepted section boundaries):

- Table block **24**, `/*[1]/*[2]/*[33]/*[1]/*[1]/*[1]`: Part I – Financial informationPageItem 1.Financial StatementsConsolidated Financial Statements – JPMorgan Chase & Co.:Consolidated statements of income (unaudited) for the three months ended March 31, 2026 and 202580Consolidated statements of comprehensive income (unaudited) for the three months ended March 31, 2026 and 202581Consolidated balance sheets (unaudited) at March 31, 2026 and December 31, 202582Consolidate […]
  - “Part I – Financial information” → `#i1468582547144a00ae69bd4661b9ea50_19`; source target: `/*[1]/*[2]/*[35]` (div; ).
  - “Financial Statements” → `#i1468582547144a00ae69bd4661b9ea50_169`; source target: `/*[1]/*[2]/*[599]` (div; ).
  - “Consolidated Financial Statements – JPMorgan Chase & Co.:” → `#i1468582547144a00ae69bd4661b9ea50_172`; source target: `/*[1]/*[2]/*[603]` (div; ).
  - “Consolidated statements of income (unaudited) for the three” → `#i1468582547144a00ae69bd4661b9ea50_175`; source target: `/*[1]/*[2]/*[605]` (div; ).
  - “Consolidated statements of comprehensive income (unaudited) for the three” → `#i1468582547144a00ae69bd4661b9ea50_178`; source target: `/*[1]/*[2]/*[611]` (div; ).
  - “Consolidated statements of changes in stockholders' equity (unaudited) for the three” → `#i1468582547144a00ae69bd4661b9ea50_184`; source target: `/*[1]/*[2]/*[630]` (div; ).
  - “Consolidated statements of cash flows (unaudited) for the” → `#i1468582547144a00ae69bd4661b9ea50_187`; source target: `/*[1]/*[2]/*[638]` (div; ).
  - “Notes to Consolidated Financial Statements (unaudited)” → `#i1468582547144a00ae69bd4661b9ea50_190`; source target: `/*[1]/*[2]/*[646]` (div; ).
- Table block **25**, `/*[1]/*[2]/*[33]/*[3]/*[1]/*[1]`: PageReport of Independent Registered Public Accounting Firm168Consolidated Average Balance Sheets, Interest and Rates (unaudited) for the three months ended March 31, 2026 and 2025169Glossary of Terms and Acronyms and Line of Business Metrics170Item 2.Management’s Discussion and Analysis of Financial Condition and Results of Operations.Consolidated Financial Highlights3Introduction4Executive Overview5Consolidated Res […]
  - “Management’s Discussion and Analysis of Financial Condition and Results of Operations.” → `#i1468582547144a00ae69bd4661b9ea50_25`; source target: `/*[1]/*[2]/*[48]` (div; ).
  - “Firmwide Risk Management” → `#i1468582547144a00ae69bd4661b9ea50_67`; source target: `/*[1]/*[2]/*[224]` (div; ).
  - “Capital Risk Management” → `#i1468582547144a00ae69bd4661b9ea50_70`; source target: `/*[1]/*[2]/*[230]` (div; ).
  - “Liquidity Risk Management” → `#i1468582547144a00ae69bd4661b9ea50_88`; source target: `/*[1]/*[2]/*[284]` (div; ).
  - “Investment Portfolio Risk Management” → `#i1468582547144a00ae69bd4661b9ea50_118`; source target: `/*[1]/*[2]/*[504]` (div; ).
  - “Market Risk Management” → `#i1468582547144a00ae69bd4661b9ea50_121`; source target: `/*[1]/*[2]/*[510]` (div; ).
  - “Country Risk Management” → `#i1468582547144a00ae69bd4661b9ea50_133`; source target: `/*[1]/*[2]/*[566]` (div; ).

### 0001628280-26-054343 — 2026-06-30

[Original SEC HTML](https://www.sec.gov/Archives/edgar/data/19617/000162828026054343/jpm-20260630.htm); [exact local Bronze](../.runtime/artifacts/bronze/sha256/7c/7cbc765c34c9a43a09b74db21e75bd0f94e548b4dfb50c53699526a985935a48). Initial unclassified range: **0–2401**, 2,402 blocks (2,120 paragraphs, 273 tables, 9 headings). This range includes cover/TOC, MD&A, financial statements/notes and later supplementary material; it is not a clean semantic Item 1/2 range.

Relevant body locations (key samples include full IDs below; the separate audit records every heading ID):

- Block **38**: opaque introduction-heading table, `/*[1]/*[2]/*[53]/*[1]`. Source text: “INTRODUCTION”.
- Block **39**: preserved MD&A narrative, `/*[1]/*[2]/*[55]/*[1]/*[1]`.
- Block **1148** (paragraph): “Consolidated statements of income (unaudited)”; `/*[1]/*[2]/*[743]`; owner: unclassified; Part unknown, Item none.
- Block **1153** (paragraph): “Consolidated statements of comprehensive income (unaudited)”; `/*[1]/*[2]/*[751]`; owner: unclassified; Part unknown, Item none.
- Block **1158** (paragraph): “Consolidated balance sheets (unaudited)”; `/*[1]/*[2]/*[760]`; owner: unclassified; Part unknown, Item none.
- Block **1165** (paragraph): “Consolidated statements of changes in stockholders’ equity (unaudited)”; `/*[1]/*[2]/*[770]`; owner: unclassified; Part unknown, Item none.
- Block **1170** (paragraph): “Consolidated statements of cash flows (unaudited)”; `/*[1]/*[2]/*[778]`; owner: unclassified; Part unknown, Item none.
- Block **1177** (paragraph): “NOTES TO CONSOLIDATED FINANCIAL STATEMENTS (unaudited)”; `/*[1]/*[2]/*[790]`; owner: unclassified; Part unknown, Item none.
- Block **2402** (paragraph): “Item 3. Quantitative and Qualitative Disclosures About Market Risk.”; `/*[1]/*[2]/*[1328]/*[1]/*[1]`; owner: ambiguous; Part unknown, Item 3.
- Block **2404** (paragraph): “Item 4. Controls and Procedures.”; `/*[1]/*[2]/*[1328]/*[1]/*[4]`; owner: ambiguous; Part unknown, Item 4.
- Block **2407** (heading): “Part II – Other Information”; `/*[1]/*[2]/*[1328]/*[1]/*[8]`; owner: unclassified; Part II, Item none.
- Block **2423** (paragraph): “Item 3. Defaults Upon Senior Securities.”; `/*[1]/*[2]/*[1337]`; owner: classified; Part II, Item 3.
- Block **2425** (paragraph): “Item 4. Mine Safety Disclosures.”; `/*[1]/*[2]/*[1340]`; owner: classified; Part II, Item 4.

Table preservation check: **279/279** visible top-level source-table locations have an emitted source owner; **279** are opaque table blocks. Nested tables remain inside their retained outer HTML table. This proves locator-level table preservation on these sources, not complete financial-cell interpretation.

TOC source labels/links (navigation only; not accepted section boundaries):

- Table block **24**, `/*[1]/*[2]/*[33]/*[1]/*[1]/*[1]`: Part I – Financial informationPageItem 1.Financial StatementsConsolidated Financial Statements – JPMorgan Chase & Co.:Consolidated statements of income (unaudited) for the three and six months ended June 30, 2026 and 202593Consolidated statements of comprehensive income (unaudited) for the three and six months ended June 30, 2026 and 202594Consolidated balance sheets (unaudited) at June 30, 2026 and December 31, 2025 […]
  - “Part I – Financial information” → `#id4a989f16cde416699cc90482e29b090_19`; source target: `/*[1]/*[2]/*[35]` (div; ).
  - “Financial Statements” → `#id4a989f16cde416699cc90482e29b090_172`; source target: `/*[1]/*[2]/*[735]` (div; ).
  - “Consolidated Financial Statements – JPMorgan Chase & Co.:” → `#id4a989f16cde416699cc90482e29b090_175`; source target: `/*[1]/*[2]/*[739]` (div; ).
  - “Consolidated statements of income (unaudited) for the three” → `#id4a989f16cde416699cc90482e29b090_178`; source target: `/*[1]/*[2]/*[741]` (div; ).
  - “Consolidated statements of comprehensive income (unaudited) for the three” → `#id4a989f16cde416699cc90482e29b090_181`; source target: `/*[1]/*[2]/*[747]` (div; ).
  - “Consolidated statements of changes in stockholders' equity (unaudited) for the three” → `#id4a989f16cde416699cc90482e29b090_187`; source target: `/*[1]/*[2]/*[766]` (div; ).
  - “Consolidated statements of cash flows (unaudited) for the” → `#id4a989f16cde416699cc90482e29b090_190`; source target: `/*[1]/*[2]/*[774]` (div; ).
  - “Notes to Consolidated Financial Statements (unaudited)” → `#id4a989f16cde416699cc90482e29b090_193`; source target: `/*[1]/*[2]/*[782]` (div; ).
- Table block **25**, `/*[1]/*[2]/*[33]/*[3]/*[1]/*[1]`: PageReport of Independent Registered Public Accounting Firm189Consolidated Average Balance Sheets, Interest and Rates (unaudited) for the three and six months ended June 30, 2026 and 2025190Glossary of Terms and Acronyms and Line of Business Metrics192Item 2.Management’s Discussion and Analysis of Financial Condition and Results of Operations.Consolidated Financial Highlights3Introduction4Executive Overview5Consolida […]
  - “Management’s Discussion and Analysis of Financial Condition and Results of Operations.” → `#id4a989f16cde416699cc90482e29b090_25`; source target: `/*[1]/*[2]/*[50]` (div; ).
  - “Firmwide Risk Management” → `#id4a989f16cde416699cc90482e29b090_70`; source target: `/*[1]/*[2]/*[344]` (div; ).
  - “Capital Risk Management” → `#id4a989f16cde416699cc90482e29b090_73`; source target: `/*[1]/*[2]/*[350]` (div; ).
  - “Liquidity Risk Management” → `#id4a989f16cde416699cc90482e29b090_91`; source target: `/*[1]/*[2]/*[403]` (div; ).
  - “Investment Portfolio Risk Management” → `#id4a989f16cde416699cc90482e29b090_121`; source target: `/*[1]/*[2]/*[633]` (div; ).
  - “Market Risk Management” → `#id4a989f16cde416699cc90482e29b090_124`; source target: `/*[1]/*[2]/*[639]` (div; ).
  - “Country Risk Management” → `#id4a989f16cde416699cc90482e29b090_136`; source target: `/*[1]/*[2]/*[698]` (div; ).

**Neighboring ownership:** No earlier classified item owns the initial unclassified range, and no Part II item absorbs it. The first ambiguous Item 3 begins immediately after the initial range; Item 4 and the explicit Part II transition follow. Unknown material shares a broad unclassified owner with cover/navigation and other report material, so claiming a precise semantic section from that owner would still be incorrect. All emitted blocks remain present and singly owned. These checks do not prove losslessness for every recovered narrative text node.

**WP3.3 impact:** Source table access and document lineage survive. Table extraction can proceed by enumerating table blocks across every classification state and retaining null/ambiguous section context; selecting only classified I:1 would drop JPMorgan financial tables. Table semantics, financial headers/units/footnotes and nested grids still need WP3.3 validation. If the proposed WP3.3 design requires every table to have a known item, this becomes a blocker to that design and must be resolved before that assumption is implemented.

**Future RAG impact:** Item-filtered queries for I:1/I:2 would under-retrieve both quarters; broad section-sized chunks would mix MD&A, notes and unrelated content. Chunking must enforce independent size limits, preserve physical block order and unknown classification, and avoid upgrading TOC/reference text into semantic truth. Correct semantic membership, broader labels and human review should gate any complete section-filtered retrieval claim. JPMorgan annual incorporation-by-reference/annex material has a related physical-versus-semantic limitation.

## Risks and recommended fixes

| Severity | Finding and evidence | Recommendation / gate |
| --- | --- | --- |
| High for section-filtered RAG; moderate for WP3.3 | Two JPMorgan quarters lack I:1/I:2; 4 Items 3/4 have unknown part; broad unclassified ranges preserve content. | In a separately authorized parser/semantic-mapping package, add source-validated reference/anchor handling and regression labels for both layouts. Preserve physical ranges and allow noncontiguous semantic membership; never silently assign these blocks to adjacent items. WP3.3 must not filter them out. |
| Moderate | The 25 selected labels are agent-authored and cover seven filings; new samples also lack human adjudication. | Have a human adjudicate the samples and start/end anchors, record disagreements and version any corrected labels. Expand coverage before generalization claims. Preserve the current frozen benchmark as historical evidence. |
| Moderate | HTML recovery and opaque narrative/layout tables limit completeness and discoverability. | During WP3.3 validate nested tables, headers, units, scales, signs and footnotes against source. Preserve source owners and warnings; avoid calling a resolvable marker extracted financial text. |
| Low for bounded acceptance; moderate at larger workloads | Reproducibility is demonstrated only on this Windows backend; no adversarial worst-case resource benchmark or watchdog evidence. | Keep backend versions pinned; measure memory/CPU and cross-platform results before broader operational guarantees. |

No unexplained failing repository assertion or blocking source-integrity defect was found. No fix was made during this review.

## Reproducibility record

Environment: Python **3.12.14**, uv **0.12.23**, lxml **6.1.3**, libxml **2.11.9**, Windows. Parser identity: `sec-html-1/lxml-(6, 1, 3, 0)/libxml-(2, 11, 9)/sec-sections-1`; pipeline `html-1`, envelope `html-result-1`, canonical records `canonical-1`.

The fresh corpus runner parsed each original twice, compared logical bytes and revalidated serialized results. The separate audit compared the new artifacts with the completion-run artifacts for all 18 filings: complete logical serialization, stable IDs, block order, section ownership/ranges and SHA-256 all match. Logical bytes exclude the fetch-occurrence provenance row; operational `executed_at_utc` and per-filing `diagnostic_seconds` are excluded from diagnostic comparisons. Source filing publication/acceptance dates remain semantic input and are not stripped. Original provenance was separately validated rather than treated as dispensable lineage.

- Corpus split SHA-256: `70ee567c6ab2800b90dfff912bffea80c4a481fcd3f496bcb8c1a3d4c2df1093` (unchanged).
- Boundary labels SHA-256: `12b7fb19bab1a6992bd73295a30281ebb6ed1af5c85b537e6cda119eab5c0fea` (unchanged).
- Dependency lock SHA-256: `a1ed09e39c11c15fb1dcc4fbca289633d80862eb3012f44a62d71160665d9fed` (unchanged).
- All six pre-held-out freeze entries match after the documented CRLF→LF normalization. All source-code hashes in the completion diagnostics match the new run. Per-document source/logical hashes are listed below.

Held-out boundary register (source start and immediately-next-heading end convention; all seven unchanged):

| Accession | Item | Inclusive block range | Source start XPath | Next heading XPath |
| --- | --- | --- | --- | --- |
| 0000320193-26-000020 | I:1 | 42–152 | `/*[1]/*[2]/*[58]` | `/*[1]/*[2]/*[167]` |
| 0000320193-26-000020 | I:2 | 153–241 | `/*[1]/*[2]/*[167]` | `/*[1]/*[2]/*[295]` |
| 0000320193-26-000020 | II:1A | 261–287 | `/*[1]/*[2]/*[322]` | `/*[1]/*[2]/*[356]` |
| 0001193125-26-323660 | I:1 | 38–254 | `/*[1]/*[2]/*[11]/*[4]` | `/*[1]/*[2]/*[55]/*[1]` |
| 0001193125-26-323660 | I:1A | 255–439 | `/*[1]/*[2]/*[55]/*[1]` | `/*[1]/*[2]/*[115]/*[1]` |
| 0001193125-26-323660 | II:7 | 491–755 | `/*[1]/*[2]/*[135]/*[1]` | `/*[1]/*[2]/*[195]/*[1]` |
| 0001193125-26-323660 | II:8 | 773–1299 | `/*[1]/*[2]/*[199]/*[1]` | `/*[1]/*[2]/*[355]/*[1]` |

## Test execution and commands actually run

Commands ran from the repository root. `bash` below means `C:/Program Files/Git/bin/bash.exe`; native Python means `.venv/Scripts/python.exe`. Public disposable development credentials came from `docs/development.md`; no private environment values were read. The test URL targeted the dedicated `sec_research_test` database; fixtures created/dropped uniquely named disposable databases, without migrating/deleting the configured connection database.

```bash
export TEST_DATABASE_URL='postgresql+psycopg://sec_research:sec_research_dev@127.0.0.1:5432/sec_research_test'
export PYTEST_ADDOPTS='-o cache_dir=.runtime/pytest-wp32-acceptance'
bash scripts/check.sh
.venv/Scripts/python.exe -m sec_research.processing.corpus --split all --output .runtime/wp32-acceptance/replay.json
bash scripts/verify-wheel.sh
.venv/Scripts/python.exe .runtime/wp32_acceptance_audit.py
.venv/Scripts/python.exe .runtime/wp32_acceptance_report.py
.venv/Scripts/python.exe .runtime/wp32_acceptance_validate.py
git diff --check
git status --short
```

- **Passed:** `check.sh` exit 0: lock resolves 44 packages; Ruff lint passes; **62 files** already formatted; strict mypy passes **59 source files**. Pytest collected/executed **260**, **260 passed in 17.33 seconds**, **0 failed, 0 skipped, 0 xfailed, 0 deselected**. Branch-aware coverage **92%** (diagnostic, not an accuracy score). Includes 10 actual PostgreSQL integration tests and eight offline LocalBronze parser integration cases.
- **Passed:** corpus CLI exit 0; 18 parsed; all reported source/graph/boundary/replay assertions succeeded. A separate successful audit verifies the same counts and the unchanged original logical outputs. The reporting script validates sample source containment and JPMorgan table-preservation assertions before writing this report.
- **Passed after retry:** wheel/sdist build; clean temporary environment; 24 runtime distributions installed with required hashes; project wheel installed; contracts/parser replay/API/CLIs/typing marker verified outside the checkout. Pins, TLS and artifact hashes remained enforced.
- **Initial execution errors, resolved:** wheel build initially exited 2 because sandbox network access denied the pinned Hatchling fetch from PyPI (`os error 10013`); the network-enabled retry exited 0. The separate review script initially exited 1 after its per-filing checks due to a reviewer-only `aggregates`/`metrics` diagnostic-key typo; corrected that temporary script and reran all of its assertions. The sample generator initially rejected an Amazon layout-heading comparison because source cell text concatenation differs from the parser’s documented cell-separator whitespace; the review helper now also verifies that representation against the same source cells. Final review helpers exited 0. No implementation or repository test changed.
- **Final document checks:** `git diff --check` and local Markdown/evidence validation are recorded in the final verification note below.
- **Unrun / not claimed:** independent human adjudication, whole-corpus section precision/recall, financial-cell correctness, retrieval/model evaluation, cross-platform replay, worst-case resource testing, hosted CI and container rebuild/start. No tests were intentionally skipped or expected to fail in the executed full suite.

Local evidence retained (ignored, not published datasets): [fresh replay](../.runtime/wp32-acceptance/replay.json), [separate audit](../.runtime/wp32-acceptance/independent-audit.json), [sample records](../.runtime/wp32-acceptance/human-review-samples.json), [JPMorgan table check](../.runtime/wp32-acceptance/table-preservation.json), [test log](../.runtime/wp32-acceptance-check.log), [initial wheel log](../.runtime/wp32-acceptance-wheel.log), [successful wheel log](../.runtime/wp32-acceptance-wheel-retry.log), [audit script](../.runtime/wp32_acceptance_audit.py), [report-generation script](../.runtime/wp32_acceptance_report.py). These local links require this checkout; original SEC links and exact source hashes below support external source identification.

## Per-filing section extraction register

All block ordinals are zero-based and inclusive. **Start/end IDs below are full stable block IDs**, including one-block ranges. Every identified range is listed, including unclassified/ambiguous material. `S0`, `S1`, etc. are readable section-ordinal aliases within that document, not replacement persistent identifiers. Section titles are source text; long cover titles are abbreviated explicitly. Missing priority labels refer to the parser’s documented finite priority set, not a legal disclosure-completeness judgment. Other absent form labels are reported only as undetected labels; applicability is not adjudicated. Provenance PASS means checksum/length/metadata/document/filing/fetch linkage, graph revalidation and all emitted locators pass; it does not assert semantic section accuracy.

| Filing | Company | Accession | Form | Blocks | Ranges / classified | Missing priority labels | Warning events | Provenance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F01 | JPMorgan Chase & Co. | 0001628280-26-008131 | 10-K | 4,596 | 25 / 21 | none | 6 | PASS |
| F02 | JPMorgan Chase & Co. | 0001628280-26-029344 | 10-Q | 2,277 | 12 / 7 | I:1, I:2 | 9 | PASS |
| F03 | JPMorgan Chase & Co. | 0001628280-26-054343 | 10-Q | 2,445 | 12 / 7 | I:1, I:2 | 9 | PASS |
| F04 | Apple | 0000320193-24-000123 | 10-K | 717 | 29 / 23 | none | 8 | PASS |
| F05 | Apple | 0000320193-25-000079 | 10-K | 706 | 29 / 23 | none | 8 | PASS |
| F06 | Apple | 0000320193-26-000013 | 10-Q | 320 | 15 / 11 | none | 6 | PASS |
| F07 | Apple | 0000320193-26-000020 | 10-Q | 312 | 15 / 11 | none | 6 | PASS |
| F08 | Microsoft | 0000950170-25-100235 | 10-K | 1,401 | 29 / 23 | none | 8 | PASS |
| F09 | Microsoft | 0001193125-26-323660 | 10-K | 1,401 | 29 / 23 | none | 8 | PASS |
| F10 | Microsoft | 0001193125-26-027207 | 10-Q | 881 | 13 / 9 | none | 6 | PASS |
| F11 | Microsoft | 0001193125-26-191507 | 10-Q | 894 | 13 / 9 | none | 6 | PASS |
| F12 | Amazon | 0001018724-26-000004 | 10-K | 1,017 | 29 / 23 | none | 8 | PASS |
| F13 | Amazon | 0001018724-26-000014 | 10-Q | 619 | 15 / 11 | none | 6 | PASS |
| F14 | Amazon | 0001018724-26-000026 | 10-Q | 639 | 15 / 11 | none | 6 | PASS |
| F15 | Alphabet | 0001652044-25-000014 | 10-K | 1,380 | 29 / 23 | none | 8 | PASS |
| F16 | Alphabet | 0001652044-26-000018 | 10-K | 1,334 | 29 / 23 | none | 8 | PASS |
| F17 | Alphabet | 0001652044-26-000048 | 10-Q | 692 | 13 / 9 | none | 6 | PASS |
| F18 | Alphabet | 0001652044-26-000071 | 10-Q | 822 | 13 / 9 | none | 6 | PASS |

### F01 — JPMorgan Chase & Co. — 0001628280-26-008131 — 10-K

- Filing date **2026-02-13**; report date **2025-12-31**; split **development**; **4,596 blocks**, **25 detected ranges** (21 classified, 0 ambiguous, 4 unclassified).
- Document ID: `document:a514e8bfa0c42823090ba32aa168d0e9a4e5c00b7167084673212ddf4620b956`.
- Source: [jpm-20251231.htm](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/42/428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05); 12,927,431 bytes; SHA-256 `428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05`.
- Logical output SHA-256: `d2bd81ad3a4dfe53b68e54059e190267c5f57d4d2cea9e77e3b6f49b42883ceb`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **4,596/4,596** locators; fetch `79aa1c4d-831a-4239-a224-6e82e7fa6a5e`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): III:14, IV:16.
- Unclassified/ambiguous ranges: S0 0–29 (unclassified; Part unknown, Item none); S1 30–30 (unclassified; Part I, Item none); S23 895–4589 (unclassified; Part IV, Item none); S24 4590–4595 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×2, `non_item_section` ×1; total **6**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | UNITED STATES | 0–29 | `block:5cdf998729f80d5a58b8fbc663876429e9fe7691a547476169a39a5e61587a96` | `block:9d9513d4e336d94985ffeaa68210ebc0a766f4bb30aa2559e73e1c823ccc02f1` |
| S1: unclassified; Part I, Item none | Part I | 30–30 | `block:527ed9e2a853ab2ddd43d6fc2e5338ee503d6cd36fac59507c6b39b83848bd2b` | `block:527ed9e2a853ab2ddd43d6fc2e5338ee503d6cd36fac59507c6b39b83848bd2b` |
| S2: classified; Part I, Item 1 | Item 1. Business. | 31–134 | `block:65c9fd5eeeed08c617c0229132118fe690e365b3d0969ef9ea050df2f223f741` | `block:927229256eec30eefa8185bb95d0f79d847ba789b644ce81f5cc35df0eb984db` |
| S3: classified; Part I, Item 1A | Item 1A. Risk Factors. | 135–802 | `block:d5040d438cdcf975c47c99a302acc28bf8f624e51cc560942b391a9534601a46` | `block:081be521bf298bf05aec9e744b5d389a5c8c946c2cd7e6ea86a0a28dcc0da110` |
| S4: classified; Part I, Item 1B | Item 1B. Unresolved Staff Comments. | 803–804 | `block:42458252e05604b69740bae0ea236e7f69ee4d17ac73cf1e934a199f7a26dfd8` | `block:ff4c06cf9c47f1d475f2720fb9244825d8d180878b72b99821bd75e3857c9d2c` |
| S5: classified; Part I, Item 1C | Item 1C. Cybersecurity. | 805–806 | `block:d890906dd77181ad952469c27843c5072e7d92e000111032d1bf9a3b317b0f1a` | `block:c52b2305898ad0430068a26e391341f313e6aa907d607b25bf34bde6592cae14` |
| S6: classified; Part I, Item 2 | Item 2. Properties. | 807–813 | `block:fc275808d6e2c93a8b098e611b1624f3d97d667685772ba060ca2591d0a5e9d1` | `block:de5434115af67e24ee1e42ba87a8c265ea1b7a0c260878f17bb715f4321394bf` |
| S7: classified; Part I, Item 3 | Item 3. Legal Proceedings. | 814–815 | `block:fdbb36b172cddf29b5ce2b3a21494af4c2d4f0c5d3a4f2dcbc8bb6cf341d2087` | `block:5cc8460d958cbcad8fd472cf684986734e42e80af70d543f06be6f8a97e5fb67` |
| S8: classified; Part I, Item 4 | Item 4. Mine Safety Disclosures. | 816–818 | `block:4c0838384ba2a1e01ad8038e85903ea6b9eb5e528b4b46e114279e35f0452c48` | `block:38495e4d41bd8ec764d1809fd0580475b410b56c822b8494ad8de5b2c0a933d6` |
| S9: classified; Part II, Item 5 | Item 5. Market for Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of E […] | 819–830 | `block:d5480fabb3198d59be736333ee90d45b5b0643359a82c1f7776050729f5c90a0` | `block:dd56ed079ffb8c619753ca189f53c2f50c71328df2968904e9d8a32ba44f61ea` |
| S10: classified; Part II, Item 6 | Item 6. Reserved | 831–831 | `block:c5cdfbe8769f1dbb1b7a87f2f18eb184ca184423b6ea44dc6f6eac2a6da0eba5` | `block:c5cdfbe8769f1dbb1b7a87f2f18eb184ca184423b6ea44dc6f6eac2a6da0eba5` |
| S11: classified; Part II, Item 7 | Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations. | 832–833 | `block:ff6c41de26cdc5478b5ee78a1654e6b153fb3725aa5af2fadb9eb9c4b4d572be` | `block:0172b1862e703cc4601d2549021e55b4b0a8b0116588d91bb56bff064a052447` |
| S12: classified; Part II, Item 7A | Item 7A. Quantitative and Qualitative Disclosures About Market Risk. | 834–837 | `block:bc51b54f7bffcddde01e64c09edfc72b4ed9d7b13d58a502fa20604ba4641bbf` | `block:2d5c204819fb76e1c9cee573d15d0309df92c86860cda710148403771735604b` |
| S13: classified; Part II, Item 8 | Item 8. Financial Statements and Supplementary Data. | 838–840 | `block:3c13d4aed94bac6643a12975a182682c7f957832223de101f926e8cd70035cc8` | `block:94a06aa6d10d8c1b13fb7d48d25eebb3c8fc068dc78c665192a0c81429255286` |
| S14: classified; Part II, Item 9 | Item 9. Changes in and Disagreements With Accountants on Accounting and Financial Disclosure. | 841–842 | `block:9ded032fb4b4c175f5a8c5d1e6cf2c39eafc319b2b51bd85d67227a78254dc3c` | `block:03cca292615fa6a77f82cd3c9484d53bebefea7ad139e4bbddcb5c07501b4aef` |
| S15: classified; Part II, Item 9A | Item 9A. Controls and Procedures. | 843–848 | `block:0123486c204cb7c30b82d0aa10a2b214d09507184a30185f7c0aaefb566c0010` | `block:58a2e1f8819ed9d9e015042d410cf248f1720729e9844d9f51b2574e43ccb65a` |
| S16: classified; Part II, Item 9B | Item 9B. Other Information. | 849–863 | `block:c40a287ffd0acb036b1b6c0792b884084b48fe956f15761530ff206d7179987d` | `block:cbbec4c13157b7bf999c5f2cc82984e1c269b4e028fa0ab9ed217b1c8b427db5` |
| S17: classified; Part II, Item 9C | Item 9C. Disclosure regarding Foreign Jurisdictions that Prevent Inspections. | 864–866 | `block:201bd98c60ef374219216f32a504bb929be282f93fa4904df73bb2cfe0ae4460` | `block:d8de86d44f7c89130c50a8e17508fc9aeb002c9c151b5c09c0c0d298f243166e` |
| S18: classified; Part III, Item 10 | Item 10. Directors, Executive Officers and Corporate Governance. | 867–876 | `block:a0c70ff13d2b1fd19052c5c8e105b2f1e6b69027f6c074390f9e8c30fe53cc54` | `block:5531a11cebbed0127264a353a0dd275a3e460dd80fb0c92b57933317cca2811b` |
| S19: classified; Part III, Item 11 | Item 11. Executive Compensation. | 877–878 | `block:eb34f73a71ba7df139bf2e8065f3f1c4ad89e852b2437657ca36d66f67e078d0` | `block:15463e4e42e927d640cf1fa96106848c808392a659f8f53a9c9fdfc00fe217df` |
| S20: classified; Part III, Item 12 | Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matt […] | 879–885 | `block:e516e7409130583527f9dbf3b4e50c814a4e8b303a49c6e2e218edeb962fb6ac` | `block:bbcbd1e4136d8dcf9d65dec507d6147465b2df7e6d71a26bd3a1e54f081ba271` |
| S21: classified; Part III, Item 13 | Item 13. Certain Relationships and Related Transactions, and Director Independence. | 886–890 | `block:beb4769e18cd387abcb4c0ffcc3ac999098f91f80b03bc4abb3b8d396dd2e86e` | `block:bc4dd745447078fe9d705ba5ce5a237e9d3a6e390ebdb7210c3cdedd914102e1` |
| S22: classified; Part IV, Item 15 | Item 15. Exhibits, Financial Statement Schedules. | 891–894 | `block:6628b4641b3ed9cebf138fe72299d3c80b165bf3cd523e39a52e7b02302682b7` | `block:b422e1ab01175876761ec316ca21e31331fade5aadcdeefbcc1b6ba52f4a073a` |
| S23: unclassified; Part IV, Item none | Part IV | 895–4589 | `block:0d4cfe2956a7bf1cd4226554181a6d19938e8a1c131c46c4bb613bf85a6f8e11` | `block:8e89bdceb99a53130047b436aab7f4235c011f8aecc6714b80619fe5a7f6cb22` |
| S24: unclassified; Part unknown, Item none | Signatures | 4590–4595 | `block:c9977aad9dcc19e7d472f1af2800189798649976b0a2cb7f9025231c3b374c74` | `block:e597f6b41958d0a5dfb386c933e8d2e14425361cbd33d64e8a93d59944a0f278` |

### F02 — JPMorgan Chase & Co. — 0001628280-26-029344 — 10-Q

- Filing date **2026-05-01**; report date **2026-03-31**; split **development**; **2,277 blocks**, **12 detected ranges** (7 classified, 2 ambiguous, 3 unclassified).
- Document ID: `document:3150c4203a3994c1a0a4b2d65550a0a25942c608f619840f0234683a77756351`.
- Source: [jpm-20260331.htm](https://www.sec.gov/Archives/edgar/data/19617/000162828026029344/jpm-20260331.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/19/19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc); 9,164,716 bytes; SHA-256 `19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc`.
- Logical output SHA-256: `43054dd5e3c313a1c6790dc2d7bd556528d23e9320a51f2d54c9c872252d6b88`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **2,277/2,277** locators; fetch `82b3ab7c-4be8-4913-8d7c-8a4473d67406`; source links and section/block graph revalidated.
- Missing priority sections: **I:1, I:2**. Other undetected form labels (including ambiguity): I:3, I:4.
- Unclassified/ambiguous ranges: S0 0–2233 (unclassified; Part unknown, Item none); S1 2234–2235 (ambiguous; Part unknown, Item 3); S2 2236–2238 (ambiguous; Part unknown, Item 4); S3 2239–2239 (unclassified; Part II, Item none); S11 2271–2276 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `missing_part` ×2, `part_preamble` ×1, `non_item_section` ×1, `missing_priority_i_1` ×1, `missing_priority_i_2` ×1; total **9**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | UNITED STATES | 0–2233 | `block:952b5cdd50ffddef4ffa37c9e9aad4e97382170ec5531bbb8c8a2dfbe51190fc` | `block:dffa9834f075a00336f92a903aec58e2ef7abcf99f9423bcee9e60d89cf8eb41` |
| S1: ambiguous; Part unknown, Item 3 | Item 3. Quantitative and Qualitative Disclosures About Market Risk. | 2234–2235 | `block:a54296a2c8f09cb4dd494691ad7d337bd48195e5cda30cf708bfb0a8958a44c7` | `block:1325b93c68ee1130a452e6be8b6d405c714071f744e2c281052ecfb76e4603ca` |
| S2: ambiguous; Part unknown, Item 4 | Item 4. Controls and Procedures. | 2236–2238 | `block:ede7582649442d4fc452698cc399ba03c0b91c4eab05fb798d46f51f73303d06` | `block:c8a447b0e521381f18d91e21b5c17ea6d3751d8a344d1eccdc275776f5290bc4` |
| S3: unclassified; Part II, Item none | Part II – Other Information | 2239–2239 | `block:4a8336220f4644614813e4124b3df606e230ea1fe3dd2fa00b6d706047148c5c` | `block:4a8336220f4644614813e4124b3df606e230ea1fe3dd2fa00b6d706047148c5c` |
| S4: classified; Part II, Item 1 | Item 1. Legal Proceedings. | 2240–2241 | `block:9fc5942dd049456f333df976ae5a28f66d09746cbee4e4cbefc4426f381bc518` | `block:2aa855d75324931c5488a12b7d772352d1ec545ed8168bd42250977096cbe2ac` |
| S5: classified; Part II, Item 1A | Item 1A. Risk Factors. | 2242–2245 | `block:9328e71b95a35310a72d6fdcbe35f64fe2bfcbe176f574e6bd9f91efc6473318` | `block:0a9ba3c53f9fb564046dc991d0953c744ee635c8c6977a2849d5f82836e28e10` |
| S6: classified; Part II, Item 2 | Item 2. Unregistered Sales of Equity Securities and Use of Proceeds. | 2246–2254 | `block:9703e974a02a5128cda0d3c0cc8f90f3bd5c52dee88e45cfc34b4747a8ccfb45` | `block:1959cd30c3ddcd3353663d3fb4ef14df92ffae9a21959739c9e72b94543229e7` |
| S7: classified; Part II, Item 3 | Item 3. Defaults Upon Senior Securities. | 2255–2256 | `block:552eca26f47287a4a275ab9e727c08378ae1b4a9ddce3d495b868590299131ea` | `block:431f55b6010b4a44d58c6907429f241c12f6606a51d660f18f5a8fb9040b2c93` |
| S8: classified; Part II, Item 4 | Item 4. Mine Safety Disclosures. | 2257–2258 | `block:e851ff4ad342eaf6316b7a157a3dc9226bba9402d4459df417fc0aa27d6a6bfd` | `block:7bb256a4e95c8ecda4447679f1562e84de1bf9bd2ebd579fb4bd63557a2c0619` |
| S9: classified; Part II, Item 5 | Item 5. Other Information. | 2259–2264 | `block:53689a2aa9642611fc201363e56db5e4ef69d449832f9cb644715eb55134354a` | `block:187a917f329ba8225e416aedde5bb10a302bef7a78f63e493d7a638e168b28f8` |
| S10: classified; Part II, Item 6 | Item 6. Exhibits. | 2265–2270 | `block:f571c77e9723c3fecf740e1c3950880c98f5a9e330537131f96b2e83ecd799d6` | `block:1366abd589084212344d24d05d5f15dd780a9e65f0199cbc015892adc9e46fb3` |
| S11: unclassified; Part unknown, Item none | SIGNATURE | 2271–2276 | `block:aa9754b3892709a6dfeceb256256840b3bc3b6b9354cb728abe2ada23ef37937` | `block:e43dca3e69c9471ea328e6ee399499954a847f44371fb7be3aceb66d098e3a38` |

### F03 — JPMorgan Chase & Co. — 0001628280-26-054343 — 10-Q

- Filing date **2026-08-06**; report date **2026-06-30**; split **held_out**; **2,445 blocks**, **12 detected ranges** (7 classified, 2 ambiguous, 3 unclassified).
- Document ID: `document:c768c0527dfc3d9b11170ed9d378db4aacd6da9c3b62710e6f78ca13432fc8c1`.
- Source: [jpm-20260630.htm](https://www.sec.gov/Archives/edgar/data/19617/000162828026054343/jpm-20260630.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/7c/7cbc765c34c9a43a09b74db21e75bd0f94e548b4dfb50c53699526a985935a48); 11,513,980 bytes; SHA-256 `7cbc765c34c9a43a09b74db21e75bd0f94e548b4dfb50c53699526a985935a48`.
- Logical output SHA-256: `f744a76390d173cc75c12b740a13fed530c2fd7a16b248fb1a284b41cea8a3c2`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **2,445/2,445** locators; fetch `d5670e07-37b2-4cf7-976b-7af19af0cfc9`; source links and section/block graph revalidated.
- Missing priority sections: **I:1, I:2**. Other undetected form labels (including ambiguity): I:3, I:4.
- Unclassified/ambiguous ranges: S0 0–2401 (unclassified; Part unknown, Item none); S1 2402–2403 (ambiguous; Part unknown, Item 3); S2 2404–2406 (ambiguous; Part unknown, Item 4); S3 2407–2407 (unclassified; Part II, Item none); S11 2439–2444 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `missing_part` ×2, `part_preamble` ×1, `non_item_section` ×1, `missing_priority_i_1` ×1, `missing_priority_i_2` ×1; total **9**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | UNITED STATES | 0–2401 | `block:7561ba16a4dfd77ecd8f3f234b84007c6232c9479d747f1a458b418529dce548` | `block:82771070bb3a1ff8747a7c0dd437bfae9232ccea2a3aeff1bce718559fc3f9a2` |
| S1: ambiguous; Part unknown, Item 3 | Item 3. Quantitative and Qualitative Disclosures About Market Risk. | 2402–2403 | `block:9e23743017e6d295c171128c185d1ef5f062da950d74fb60049cc1a636feb3bd` | `block:424fb00eb10d92cc53f1e6a1266e4a7e669ced7a374dfb77edc69213c07dc268` |
| S2: ambiguous; Part unknown, Item 4 | Item 4. Controls and Procedures. | 2404–2406 | `block:85935e3d03d0fd2814b55545608d651c6f8b6f16c664a34f5c06f891393bb236` | `block:12308e86060949a344a897ef3e3ddae63f8dac9edff10f4899db6174aafc1074` |
| S3: unclassified; Part II, Item none | Part II – Other Information | 2407–2407 | `block:c998073908a3680333df8992b4625c1363c7f323ae27e98c9b38d7ed5bd87f1a` | `block:c998073908a3680333df8992b4625c1363c7f323ae27e98c9b38d7ed5bd87f1a` |
| S4: classified; Part II, Item 1 | Item 1. Legal Proceedings. | 2408–2409 | `block:8b3ccecbf4d4150798c961f7a9436551d4dc35873539567b33327cfe4b9bba93` | `block:1a731103d9c5affdb3313651213aac8f024e7a8ce655b7d031b0fa429b9ac3af` |
| S5: classified; Part II, Item 1A | Item 1A. Risk Factors. | 2410–2413 | `block:f97bee28bf820e86c5710619bc14ce175a2218b55580e9c43cea805fdb07f7fb` | `block:c44cd9d8f2afdcf98207bf928f63f5ad68e09ed3acbf4c9ce949d365d3d44b91` |
| S6: classified; Part II, Item 2 | Item 2. Unregistered Sales of Equity Securities and Use of Proceeds. | 2414–2422 | `block:21cfaabf72db115661839b71786ce62f8ca184854c154523f8c1a33d6e224518` | `block:044b991ae20a21469f539955f2a26c4e8f6d94227b3d285c69326ec45cbc6b8e` |
| S7: classified; Part II, Item 3 | Item 3. Defaults Upon Senior Securities. | 2423–2424 | `block:529c2f3e6a9609d8987249e88d4c51294fdeb6b8d6bc25dd7bdcc977d727eb82` | `block:d328c74cc53cfb03fd668e4344ad2ef5bc8b278a102a32419bb9db88f41a63d3` |
| S8: classified; Part II, Item 4 | Item 4. Mine Safety Disclosures. | 2425–2426 | `block:e4157fa7c9cd0b58f47ac45c5572d448237bf32a2aa7c57fbeab0c1b154b5847` | `block:79e4d22a599ffd4cda75e4f24bb5eb9d48568e7a82c080814f7f59d0728c3b5a` |
| S9: classified; Part II, Item 5 | Item 5. Other Information. | 2427–2432 | `block:8b3afe6554895ff5852dc704be66d353c1b54ad98b36c014aefae663d6cf9094` | `block:87f8ff745f2c5a718d32f65f6375daf31626b3b93713b6681b77f77942d57ad8` |
| S10: classified; Part II, Item 6 | Item 6. Exhibits. | 2433–2438 | `block:fc6fa0371cd33caca98a5aef364c7beb133072239560071297f7ed882c20b6e2` | `block:e8cdc2c0809bf8e677d09955eece9bd27678cc95599a27c6221baaa515e0c07b` |
| S11: unclassified; Part unknown, Item none | SIGNATURE | 2439–2444 | `block:c9867d6920d4bfaf4664d7ee599f4b01a4fa3f8ba645e30ab98ab11e7b263f12` | `block:31dbe0b81400ffe4e11760f8d9bb5de29b3af50c2146c89eb14e0d20900ad7a9` |

### F04 — Apple — 0000320193-24-000123 — 10-K

- Filing date **2024-11-01**; report date **2024-09-28**; split **development**; **717 blocks**, **29 detected ranges** (23 classified, 0 ambiguous, 6 unclassified).
- Document ID: `document:9c890c6cc0d4352c58b9ea63d872692317047aa7e9f10661b3203752969d64b0`.
- Source: [aapl-20240928.htm](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/87/87811e303e632b0f1843b9bc161c1b3af9c501ffec0a51a9825cc796dc369dcf); 1,503,886 bytes; SHA-256 `87811e303e632b0f1843b9bc161c1b3af9c501ffec0a51a9825cc796dc369dcf`.
- Logical output SHA-256: `382e43ae1a5ce730500251ab3b0ad994d4eeaa7c552494e7186f4a741af7c285`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **717/717** locators; fetch `e9ad532f-3305-4db2-b737-90b10bc5466d`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): none.
- Unclassified/ambiguous ranges: S0 0–53 (unclassified; Part unknown, Item none); S1 54–54 (unclassified; Part I, Item none); S9 271–271 (unclassified; Part II, Item none); S19 673–673 (unclassified; Part III, Item none); S25 686–686 (unclassified; Part IV, Item none); S28 709–716 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×4, `non_item_section` ×1; total **8**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | [TABLE] | 0–53 | `block:ddc1b4387a9928b4f9013ccf6b2fc30ac14e8361d1eb740633070136ce772618` | `block:a82ab394b71f393831668abbb99e536a04759af92fae19a841c62fa5791a18e0` |
| S1: unclassified; Part I, Item none | PART I | 54–54 | `block:3cb4330093b1443f70c5d49f6a44f883093dbd98ffca18e3f19d759518115be2` | `block:3cb4330093b1443f70c5d49f6a44f883093dbd98ffca18e3f19d759518115be2` |
| S2: classified; Part I, Item 1 | Item 1. Business | 55–120 | `block:7817d263c11f8c51e341ab836544624d8eb131acccc535f729d88385c7d49f01` | `block:c391e5b00c2c9706ec5a45988b0052213d5bf55cf13ab8e17940c2e613833565` |
| S3: classified; Part I, Item 1A | Item 1A. Risk Factors | 121–248 | `block:bc692c3848060f6bba54da6c23ffb8f0ef3546940b44d5116105e7d5447c0bc0` | `block:b50fd0b2a6bcc85e2dda15a2d976dc1683a0e6ff953af7ec674bbb5a606a791a` |
| S4: classified; Part I, Item 1B | Item 1B. Unresolved Staff Comments | 249–250 | `block:ff17a4563eda22aaa2cf89769a9c7c2e0f095b842e2991d0a014f02b8071c7bb` | `block:b3db7e6e201df4b5a3b76d0de668ad4623a0944d2409a308f180bfece5c6d80b` |
| S5: classified; Part I, Item 1C | Item 1C. Cybersecurity | 251–256 | `block:84a543dee7a6741a0b8fefad436949f8d0e264288f13f4d4c14d28158ea77fc1` | `block:1a7fae19b634c2d344c5fcb5acf44ae313fa64c74346509a111134c3e493a940` |
| S6: classified; Part I, Item 2 | Item 2. Properties | 257–258 | `block:cbb5e1fdea1bd8db4f615c2e54daa13b5c1166e85ba9d94bc1505c0671c6459a` | `block:78c2d303ff5296d43d1e334c4c64ebf773fddf0e67f7f92616c2357a7fe54c03` |
| S7: classified; Part I, Item 3 | Item 3. Legal Proceedings | 259–267 | `block:e7cb7c7ade802ff0e1fcd06011b2fda2eaeaa215172b0e70e356fe55d8443d4d` | `block:6ece455290e73a47f96337bb2bdaf0f65c67770e339b313bc7812d26811ff229` |
| S8: classified; Part I, Item 4 | Item 4. Mine Safety Disclosures | 268–270 | `block:520de8a4bc0664f20b6dece210df27473c34f73710984430dc8007ecadad1e7b` | `block:4c30f42811679c84d24aec22cfda1475a0b85a3638896c91eb0ea502f270f77c` |
| S9: unclassified; Part II, Item none | PART II | 271–271 | `block:621273054bbabe9f7653d05928ffba95508e50593fb0c85c89846caa1453ecee` | `block:621273054bbabe9f7653d05928ffba95508e50593fb0c85c89846caa1453ecee` |
| S10: classified; Part II, Item 5 | Item 5. Market for Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of E […] | 272–283 | `block:5b29b362e3b3fcaf3aaa07bbc2de323be3e1f0b99295ea27482132f2f4625d5b` | `block:cf76af92c18ab0fb8c9ad510dc2fb61ca39458d45faf0bee3f6e29345982f432` |
| S11: classified; Part II, Item 6 | Item 6. [Reserved] | 284–285 | `block:f50f2a2944eb8c50c4b1fbfa703ca3759a2f888c75ed64b5581302d79db3df24` | `block:4a343cc67589a16eb2f8f0141cbb7275862b6fe9467eccf1d81ddec9993d12e7` |
| S12: classified; Part II, Item 7 | Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations | 286–394 | `block:bb93221349d9f6c48ab7b285cbc68a269c6b04abd89b723955b948eb4277f6b4` | `block:33fe1573843474f7c8b7c0caaab0bfefbad0f3c3f1976a9b307f49237f1233aa` |
| S13: classified; Part II, Item 7A | Item 7A. Quantitative and Qualitative Disclosures About Market Risk | 395–404 | `block:5146638dc180ff0e1842b1ed0dbd19a00b54c46a73a396cad7d142875757a7f4` | `block:0a4b407e8a76b31b223fb82ca1b5ae7a5cee3f526cca9f4016b9c898abf33b91` |
| S14: classified; Part II, Item 8 | Item 8. Financial Statements and Supplementary Data | 405–650 | `block:dbb299a9033fbab11004b115f91cb12174e8fdd31d4f483e036b33c9b841b302` | `block:876349b5fac813541fd3efeba3b6331fe8ab279df984ce2e8df3c6da46696d4e` |
| S15: classified; Part II, Item 9 | Item 9. Changes in and Disagreements with Accountants on Accounting and Financial Disclosure | 651–652 | `block:a0b4d0fa4054c1a2323c27dd84b8444f1ef7e6ad0a3819b19e00215863f5769b` | `block:01cadc03bdf9b50a004c5346abcd826b0cea43ae855f831e754ead9dc6786629` |
| S16: classified; Part II, Item 9A | Item 9A. Controls and Procedures | 653–666 | `block:c91389f4dd651e8a9f450f2ef64e90a20d67048b0fd4aa846f6e378525030655` | `block:c79922c9340b201e465e86cfed7740dfe50ab30ddc726b79c3fda32c64b87696` |
| S17: classified; Part II, Item 9B | Item 9B. Other Information | 667–670 | `block:c9ee2b45e136b7a8d7679ff676527fc899291adbc4c165d8a258315988241763` | `block:04c86a3de72e2c872614693e600ca079158de25f88d6816ba390f8a5da90f01e` |
| S18: classified; Part II, Item 9C | Item 9C. Disclosure Regarding Foreign Jurisdictions that Prevent Inspections | 671–672 | `block:3712ecdfbe68355879b6709bfb53d15dfcf78914758b66f05ee9cfe4ed561cae` | `block:979aaeb83c9afa5a8528f31e69327e989df98b06b7ae8316096573e57649ddfb` |
| S19: unclassified; Part III, Item none | PART III | 673–673 | `block:a53215853beeb7706c2633f52db6842207277e06d689ee6d322f3c02cf3bba4b` | `block:a53215853beeb7706c2633f52db6842207277e06d689ee6d322f3c02cf3bba4b` |
| S20: classified; Part III, Item 10 | Item 10. Directors, Executive Officers and Corporate Governance | 674–676 | `block:b7ac78ec529b03129eb05782b43955397058c5c0249b10924d043c7be42e96ff` | `block:d2e898046d2231c8466ac763676ca2dced62512a6c1d098dbd961b0aa1b58f0f` |
| S21: classified; Part III, Item 11 | Item 11. Executive Compensation | 677–678 | `block:11714aa196963314f64a784480f0b91d8dcf61e449bad335dafb29df42501996` | `block:36d0e626767f25c6aa3e9b93f7851cb7962109b511445bf635ad6c41eb33543b` |
| S22: classified; Part III, Item 12 | Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matt […] | 679–680 | `block:9decf822e0f4d949806bce79ff6b4192162ccf00ca5bfe2d7b11d0b552cb6069` | `block:7fe5028add0f4bd9063302a87eeaa1abc8a31f21fb862e11b7390b242832a7ba` |
| S23: classified; Part III, Item 13 | Item 13. Certain Relationships and Related Transactions, and Director Independence | 681–682 | `block:1040e76b6ff22bf4e14cc90628d0e11fb72cd13956a4d621f8317ecf30d6f00e` | `block:029144c6032031273ec6c158df415f6d3eea62df29e8eb07e121fc27401952df` |
| S24: classified; Part III, Item 14 | Item 14. Principal Accountant Fees and Services | 683–685 | `block:ed8f85278bdcb4f8428459f8953944ab8d5012e8dfed914929c69a2ec1a4cbb4` | `block:e7343fda96b6a3133112c1c6348c906f5cefaa53428bc736e5f840e83ec68ebe` |
| S25: unclassified; Part IV, Item none | PART IV | 686–686 | `block:81844eb188ea9fb15a3fe283142d8ca56f1524c093f89d0a143f4ca3a7870975` | `block:81844eb188ea9fb15a3fe283142d8ca56f1524c093f89d0a143f4ca3a7870975` |
| S26: classified; Part IV, Item 15 | Item 15. Exhibit and Financial Statement Schedules | 687–705 | `block:39a36cce320258bfcc6920119d07e0c241bd49eeea2b63c8e84154c33a33c209` | `block:466bd8ea468a543819761381ebb524606ed919a4a30bd6ac82aefc9ef6a39fd3` |
| S27: classified; Part IV, Item 16 | Item 16. Form 10-K Summary | 706–708 | `block:6039e8f2e3a18aeaab037b64f0f69a6f0adfb3d23303a711fddb332de35b0c1d` | `block:77a7003844e75e2c51a269c6a4f2220fb97d790f9694a4bc68ac775b19bf3a1b` |
| S28: unclassified; Part unknown, Item none | SIGNATURES | 709–716 | `block:679af6960e85f8c48fba22b9fcf91cfc832cd7cfc0f86233a965c4da12d19329` | `block:080554494a41961469ee8c7b45dffbafc3a51183937700d0e9a048a725569efa` |

### F05 — Apple — 0000320193-25-000079 — 10-K

- Filing date **2025-10-31**; report date **2025-09-27**; split **held_out**; **706 blocks**, **29 detected ranges** (23 classified, 0 ambiguous, 6 unclassified).
- Document ID: `document:bd96e41734682d29eb59870e573b488071e1c9cd3dd743a150f2fa01f24aa261`.
- Source: [aapl-20250927.htm](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/f7/f7569b9a9cb9010780bdbf3ea89120dd2d7928caa8fff1305ace90630ca627ce); 1,520,314 bytes; SHA-256 `f7569b9a9cb9010780bdbf3ea89120dd2d7928caa8fff1305ace90630ca627ce`.
- Logical output SHA-256: `b646491850b1201228d4dccc813a9718f8f6eb23263e97137100b1b1418f2757`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **706/706** locators; fetch `c26008c5-f79a-4339-9f06-a3d6bbc4eb9a`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): none.
- Unclassified/ambiguous ranges: S0 0–53 (unclassified; Part unknown, Item none); S1 54–54 (unclassified; Part I, Item none); S9 253–253 (unclassified; Part II, Item none); S19 663–663 (unclassified; Part III, Item none); S25 675–675 (unclassified; Part IV, Item none); S28 698–705 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×4, `non_item_section` ×1; total **8**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | [TABLE] | 0–53 | `block:9b9556933ad894ac6b82cf33f7f8e3c25e0f56515315e021f4d9bcbfffb7195b` | `block:1ae86adfda1534e93385a76d0e54775b24e3694614ea4ccf55df046cc66beff1` |
| S1: unclassified; Part I, Item none | PART I | 54–54 | `block:b32f4083cd5f1ac028080eb99e4a7ead82ab23d8546335e6829662a2b19ecebc` | `block:b32f4083cd5f1ac028080eb99e4a7ead82ab23d8546335e6829662a2b19ecebc` |
| S2: classified; Part I, Item 1 | Item 1. Business | 55–111 | `block:73e354e356187310f7302000c80a8f2876058c3698178ac4a6fd9ef3fd0e07bf` | `block:8958d1eee38bf73a17faec1f024b43dcccaeaded1523590ac41e64ea8323dafd` |
| S3: classified; Part I, Item 1A | Item 1A. Risk Factors | 112–230 | `block:50c50934403ea40369b9a5f3aa0d63b82bc0abb4bf3d8bed260160975d1bca6b` | `block:0b6bc062a378fd6320b196e09e2f3bacc2652cd033618a7c4c660a966a89821c` |
| S4: classified; Part I, Item 1B | Item 1B. Unresolved Staff Comments | 231–232 | `block:2f3e393ef4a82d80d7b047c3992467c122a6813463de4ccb858d02d82838dc6b` | `block:bf66f0f2469c8404bdd5947ba70484c9f069b8bfac7eb37aabc6321d6dcadee8` |
| S5: classified; Part I, Item 1C | Item 1C. Cybersecurity | 233–237 | `block:8e7768d9e588cc7cf6add382dd1cbc06ca5ad6f0c1b8e1763d7f750f7d146ae4` | `block:6f0109eac82421816dc3450f88a2cf00adb0f38983fede50fd2ae01aa1bf88a5` |
| S6: classified; Part I, Item 2 | Item 2. Properties | 238–240 | `block:2e781ab27ffc2430a825da128a32911b3f781887a4fdc2adc247680d4b9e27bb` | `block:ec71be566799fe92add1e4c63d0e6a145f689183bfbb7309726ebc38d8091989` |
| S7: classified; Part I, Item 3 | Item 3. Legal Proceedings | 241–249 | `block:e6620f56e946333db6fefdeab2a40491b8201a2ca1a3a6ceb7bccce52b865e05` | `block:c62b52e78f80a820af59146eb4f10ead11bddc6cf8b74df6ac6cd774eaf5802c` |
| S8: classified; Part I, Item 4 | Item 4. Mine Safety Disclosures | 250–252 | `block:8f8f307432a9129a5e5bc1384a125650ac153b81f6f259bb68009339d86bede3` | `block:343fa00b584e4d7e194b139c637b1b618ddb5fb7638200a0a38951735b6fa56c` |
| S9: unclassified; Part II, Item none | PART II | 253–253 | `block:2e3b810f29c0d0a127d738638719a0100d3bc5b2caa7d12abc2a1021eb21b786` | `block:2e3b810f29c0d0a127d738638719a0100d3bc5b2caa7d12abc2a1021eb21b786` |
| S10: classified; Part II, Item 5 | Item 5. Market for Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of E […] | 254–265 | `block:730bfb97944c378cd7c61a1f4f6c5f3eca163cf1d31cf55405c5dad1badbbbce` | `block:9f3e27dd38845aba3245aa372f2dcf3401839e2efe27a4f3ad440df38a7cabb6` |
| S11: classified; Part II, Item 6 | Item 6. [Reserved] | 266–267 | `block:c27f7524ba4af992dabced3f5ba2c403a80f249ca99b19a4bb4a85ee2441f3f8` | `block:96421eef4423192f1b8f89c59b5cd95389b924597eb2b5da311566c6eb561721` |
| S12: classified; Part II, Item 7 | Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations | 268–380 | `block:a0b8e398716f8b77c7c0f0d21f8dfc822121bffd741b0fb7e38231b4e88bb35a` | `block:998bac83a485676129cec3b5594aeabec69d0f28eb0ba2406590c24db24b0cc5` |
| S13: classified; Part II, Item 7A | Item 7A. Quantitative and Qualitative Disclosures About Market Risk | 381–390 | `block:16560d30a7480c75a57d6b24b265ef981c48d67f3b5db3c7e25e17774d82eea2` | `block:0e1efeef07130ced16886d95884fa446db4332e94899b70c784aac6dc493cd9a` |
| S14: classified; Part II, Item 8 | Item 8. Financial Statements and Supplementary Data | 391–640 | `block:588aec83fb36aca9020ef891e50459ec9772e5aacffa8a6fb7b1ceafbe8a29d4` | `block:f26a14906d51d31d2c6f1350d91ee74ebe273591a9e987e74587b1e6fbd78e2b` |
| S15: classified; Part II, Item 9 | Item 9. Changes in and Disagreements with Accountants on Accounting and Financial Disclosure | 641–642 | `block:c544daa2fa0e958aa202de1abc37755d547e0c3bf34fbd2c87c11676ad65d1ea` | `block:1e2268a9ba53f3439b4bff5dfa05f424be84f0d00440e0b196573703a1b90aaa` |
| S16: classified; Part II, Item 9A | Item 9A. Controls and Procedures | 643–656 | `block:a8bb98c73c8d51eb65b0f0c0143a9d15ed7c1863fa57d074edf638c5e533734f` | `block:16177062ab3736e281b136d438f5e1b0c7c219ca3163178e71d2c7f0f459a797` |
| S17: classified; Part II, Item 9B | Item 9B. Other Information | 657–660 | `block:de7155622f50ef09c5399f79ec0d1e5a73d451ddd9735b1ab438095b8aefdf00` | `block:4cfb6fd9461c620a72370b3bd0ee824c0aa3ef9169afa5f6868982884874a4ec` |
| S18: classified; Part II, Item 9C | Item 9C. Disclosure Regarding Foreign Jurisdictions that Prevent Inspections | 661–662 | `block:069ca856e9cf7666f5b314e544e807aea97d03f5b9ba6208ef2b030e06240cf3` | `block:7c57754b621791d1f02a825b42824438f85d62e848bb0fb82d747ceb8e547031` |
| S19: unclassified; Part III, Item none | PART III | 663–663 | `block:566686478ea8ac290d7f83731f6540932f12441558d8c510c4f836b2663e9a15` | `block:566686478ea8ac290d7f83731f6540932f12441558d8c510c4f836b2663e9a15` |
| S20: classified; Part III, Item 10 | Item 10. Directors, Executive Officers and Corporate Governance | 664–665 | `block:c97ad289912f46fd46a85ddd0669b84af858d10d90ddedd71ec9df070f95d600` | `block:bb5a5aebf24ac23c038eb482e8597bd289d72b799c9f2c0e1312b17966acba43` |
| S21: classified; Part III, Item 11 | Item 11. Executive Compensation | 666–667 | `block:c7fda13332f62c8a44fe510ea752147933ec708593e2d3d21d913c3666d099df` | `block:3861dd64dbe1dd067a29e74170c95e19216e74a7bc50c0c07b08b7f478724ca8` |
| S22: classified; Part III, Item 12 | Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matt […] | 668–669 | `block:8ce7c8658c65ab630b64ff85513baf359fc40048b5588b04749d8323e864a540` | `block:95a38fc597c66b7c219755e783069d080616aa631fc22e4baa76f064d0ace2a7` |
| S23: classified; Part III, Item 13 | Item 13. Certain Relationships and Related Transactions, and Director Independence | 670–671 | `block:7f43afaebeb04d8786d3cf5b9b7c24f1291d15f7afa6e1062c7de8aba0630b86` | `block:2951edba784b4fcf107180483a38dd484e848895701f02f9cce724ef78353ade` |
| S24: classified; Part III, Item 14 | Item 14. Principal Accountant Fees and Services | 672–674 | `block:974102b4f7ce6b31602340aefc0c0e18f4f606d84709018e1a19bd99b9f17d4e` | `block:66fa1b8899f10dbff4f85c80a94f9de911674454aec401e3a4fa0766b33d8a17` |
| S25: unclassified; Part IV, Item none | PART IV | 675–675 | `block:298bf65299ac24d1ed616584d7743039fe32a16bc9f71a2ab3278259790c5b10` | `block:298bf65299ac24d1ed616584d7743039fe32a16bc9f71a2ab3278259790c5b10` |
| S26: classified; Part IV, Item 15 | Item 15. Exhibit and Financial Statement Schedules | 676–694 | `block:343e7b1c1f9687caefea19651c24f225adb934acc5fb957b0257d08fe0677598` | `block:729dfa5aea79064d04b6fa404773aa5de2ca118a63db418e36904e5ec0da1cc4` |
| S27: classified; Part IV, Item 16 | Item 16. Form 10-K Summary | 695–697 | `block:92209fe4d34ac52ab8b7d9ac2087c529fee2528a1a60a94c4d7a71b10f15ef4f` | `block:9c4ea442c1b8a0e331704199d97942cc1f0babf3b144b74daeffe976c4e0cf22` |
| S28: unclassified; Part unknown, Item none | SIGNATURES | 698–705 | `block:ef2ffb6076a31020c09d9266a601473b3931eaea8239d9a3d5016185520482d4` | `block:95c9f4821c04be3ceb678d01adf92bb9140dec91cd736392a40939c80e96e290` |

### F06 — Apple — 0000320193-26-000013 — 10-Q

- Filing date **2026-05-01**; report date **2026-03-28**; split **development**; **320 blocks**, **15 detected ranges** (11 classified, 0 ambiguous, 4 unclassified).
- Document ID: `document:1a23eae96fc36db7bdb13d5c9d4ba598f41bf8b60bdd03d2e25c8a9620e97b82`.
- Source: [aapl-20260328.htm](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/7d/7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91); 999,916 bytes; SHA-256 `7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91`.
- Logical output SHA-256: `2a78b4db9659de87bf63393435256b095878bb3d93cddcae96056915148c4499`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **320/320** locators; fetch `03d9cf59-11d2-4904-8ca4-d1a626fe2034`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): none.
- Unclassified/ambiguous ranges: S0 0–40 (unclassified; Part unknown, Item none); S1 41–41 (unclassified; Part I, Item none); S6 255–255 (unclassified; Part II, Item none); S14 316–319 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×2, `non_item_section` ×1; total **6**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | [TABLE] | 0–40 | `block:af17949b2db95d2764c188063f874ad6702316343eee03d87fd52f6b4cc245b8` | `block:e7223aee761a1cbfed4e81d367e34b6eba06a1b19bf121c9390d131b22a6cfdd` |
| S1: unclassified; Part I, Item none | PART I — FINANCIAL INFORMATION | 41–41 | `block:a88d0685e47a5976bfba17c0e960ade25249b5c86b68b6e465d878936e60a301` | `block:a88d0685e47a5976bfba17c0e960ade25249b5c86b68b6e465d878936e60a301` |
| S2: classified; Part I, Item 1 | Item 1. Financial Statements | 42–150 | `block:0d6e966362da73cdc8e11ead91115d70c74b585b7c4f74e1232af3c03713f026` | `block:7feea49e49d015fdcab55d6daa6153291412d3f6dea31febac6959d59e93aa07` |
| S3: classified; Part I, Item 2 | Item 2. Management’s Discussion and Analysis of Financial Condition and Results of Operations | 151–246 | `block:7c5718267d5c67cffc330cbc0f55a06c92c34a2f29df3cd09cd82996855d8709` | `block:611166275a9999de7ce8b4fd94a9ef3699042c312b2903425a86f773e6b2abfd` |
| S4: classified; Part I, Item 3 | Item 3. Quantitative and Qualitative Disclosures About Market Risk | 247–248 | `block:e217ff7007c9ef8de8753479f7e22a650cc1dc8271b81fd509b974d303ff4a44` | `block:4c45c514dfbd1635051cea1a1f5e9648734304c9189e6060449ed151b7adad86` |
| S5: classified; Part I, Item 4 | Item 4. Controls and Procedures | 249–254 | `block:f73f2b5cb10fa1ad18971dd98f67f264c3c37b2a88756f185e7207d07bfc7363` | `block:75dc7dc90ac75667104a408eabf9d53fe0ea455b954fb93cefb8d000a27c264d` |
| S6: unclassified; Part II, Item none | PART II — OTHER INFORMATION | 255–255 | `block:a93418d1f7a02453f5b1176d04f5ff4a88b401b7586167c02191eab728e14cb9` | `block:a93418d1f7a02453f5b1176d04f5ff4a88b401b7586167c02191eab728e14cb9` |
| S7: classified; Part II, Item 1 | Item 1. Legal Proceedings | 256–265 | `block:e38fdaf92f05757d6d0ffdda61f9a70755be541339a8f02b02c0e0fc1ceb9dfd` | `block:f49919b6a71e728b6aa7890a1ba11e11a9b07efd1a46b776894163ff0387ade8` |
| S8: classified; Part II, Item 1A | Item 1A. Risk Factors | 266–296 | `block:71a44e2a4891187d06dfe79370f75d8b04d37d2e7207932726b9fe68f263c12e` | `block:c83c62020a834f6dcf914c9d14bf7b80b3a56c9692db468d3eb1cbfb962ff212` |
| S9: classified; Part II, Item 2 | Item 2. Unregistered Sales of Equity Securities and Use of Proceeds | 297–302 | `block:a15565e95dfc85f4330074b42bd21b4cecd8242da09bc4ffc86ffc82132fbd89` | `block:77d8c6da94c6c5349f891184dfc92f6ffb4803a9f840e5fc1dc20ebee2b05c7b` |
| S10: classified; Part II, Item 3 | Item 3. Defaults Upon Senior Securities | 303–304 | `block:675d94cdae8034c0130afbeeb4772cc640200f374232dc16116471ec09acb533` | `block:abdab67bdd4021e5600b694839a4e23483729fc64b6fa8c51cbbdd91e906c821` |
| S11: classified; Part II, Item 4 | Item 4. Mine Safety Disclosures | 305–306 | `block:c61a2e09e306072bb664e06352c9ba58b7e0e3dadcb951bcf99d998e1284901b` | `block:d82ee6a81b932663d1c68e7434c29b9b2797863ca4c1995aedc1a464d8e87bdf` |
| S12: classified; Part II, Item 5 | Item 5. Other Information | 307–309 | `block:b70eb530960eea62b522dd6e0c477b98d2a167fcd53f30662182a17457ca46d5` | `block:bb0b7f12c0f2ee94f2eae08538192e26716609c3fa1c62d136299bef559f3ee7` |
| S13: classified; Part II, Item 6 | Item 6. Exhibits | 310–315 | `block:8f3e67d9d50c6c99d6a59aee255ff99be425fb5a2eb523c8e47decba42cb1203` | `block:26ad7de1e45f3dcadd5f38640b223242c98762a82aa4ef9d98b1e0eb3ac1be3a` |
| S14: unclassified; Part unknown, Item none | SIGNATURE | 316–319 | `block:feff46dfb67527bfff8b9cb69efe64cd33bb22f518898143addded5cdafaca0f` | `block:5247d5a56279a9054e350cbeccc0e621e67d317bdd0aa4dc7fd0775d993c5596` |

### F07 — Apple — 0000320193-26-000020 — 10-Q

- Filing date **2026-07-31**; report date **2026-06-27**; split **held_out**; **312 blocks**, **15 detected ranges** (11 classified, 0 ambiguous, 4 unclassified).
- Document ID: `document:ee4bfa74e618853b31a655a76bd5cfd10da82bcce99a2339561f8fc12d2a4de7`.
- Source: [aapl-20260627.htm](https://www.sec.gov/Archives/edgar/data/320193/000032019326000020/aapl-20260627.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/d3/d3f1996972f6b3950fbc4fd5a47dbd20a69b360eb6136da9a752c37bbdb96dc1); 1,018,316 bytes; SHA-256 `d3f1996972f6b3950fbc4fd5a47dbd20a69b360eb6136da9a752c37bbdb96dc1`.
- Logical output SHA-256: `972389c7fd273d1009d89056577f6262f0b65e9b97b7d76a4417085077dec144`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **312/312** locators; fetch `e754759d-5f43-442a-9995-16ab09315a61`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): none.
- Unclassified/ambiguous ranges: S0 0–40 (unclassified; Part unknown, Item none); S1 41–41 (unclassified; Part I, Item none); S6 250–250 (unclassified; Part II, Item none); S14 308–311 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×2, `non_item_section` ×1; total **6**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | [TABLE] | 0–40 | `block:ee4c127adc4a260c3306be6935db6d13dd4f5e8aeffd4c7ede2bccd2dd694443` | `block:af5936b8c131d2d00cee4c3a10256d6e05f7053c4c61d7ca4126d26b1857866e` |
| S1: unclassified; Part I, Item none | PART I — FINANCIAL INFORMATION | 41–41 | `block:5d7cda8bca639849fcef30af4e9ecca14bd18cd55ecd4b9cc2508400258d8138` | `block:5d7cda8bca639849fcef30af4e9ecca14bd18cd55ecd4b9cc2508400258d8138` |
| S2: classified; Part I, Item 1 | Item 1. Financial Statements | 42–152 | `block:8eb2fc0178db83daf5f3a1cec783addf711690465cd7b5aa6eae6ac60622656d` | `block:b21bf37507268feabd1622a48c916bba656b1011892608d313d74f1371de1dc2` |
| S3: classified; Part I, Item 2 | Item 2. Management’s Discussion and Analysis of Financial Condition and Results of Operations | 153–241 | `block:6f29ceac30599e1b35c0626d9f51ed6dd9fd850b32bffa9fd7cc262ad12820dc` | `block:b6abe5654293a0bbee8a569f1653789ff197d0b9710c3fb3969cca851af0fba2` |
| S4: classified; Part I, Item 3 | Item 3. Quantitative and Qualitative Disclosures About Market Risk | 242–243 | `block:cfc950a670a94dc5e224f31d32bd9bc8027c4e41a68952125a1b22473d918868` | `block:4b856e453ee54405a725e3234a21d3e66b5f236880456419fd9a3fe27d5a6481` |
| S5: classified; Part I, Item 4 | Item 4. Controls and Procedures | 244–249 | `block:b77efe62d1244a5b1531583954b9389439f0325c2c52aa1f5817529d203d615e` | `block:a96cb111b3bf93fd8b324f007fc1e5e266ff7bd969e270358fe4fef096ba41db` |
| S6: unclassified; Part II, Item none | PART II — OTHER INFORMATION | 250–250 | `block:0d9b10e7ff744b57028a0e05c68492c454aebf75db53f0195a5a1025e86c6b2a` | `block:0d9b10e7ff744b57028a0e05c68492c454aebf75db53f0195a5a1025e86c6b2a` |
| S7: classified; Part II, Item 1 | Item 1. Legal Proceedings | 251–260 | `block:bcd05ddd52bd368d1a95035d4bcedc8e11ad001d824c93238b696d6748a3b76c` | `block:06e70469774c2139687613655b108a50f11e7a1104702d5ab5747e04c404c878` |
| S8: classified; Part II, Item 1A | Item 1A. Risk Factors | 261–287 | `block:c62306a879037a1b61e02a54d67a1bcef7e9219199e6fbeb7290c728d671a08a` | `block:2a91c8b233dd10c33177767275efe928084701f0296082ceff7505389ac9a7bc` |
| S9: classified; Part II, Item 2 | Item 2. Unregistered Sales of Equity Securities and Use of Proceeds | 288–293 | `block:410783076e7883061bbbad5dd7536bf4ca75cc688e0522764be394b360171124` | `block:8ae0eefe672cecda60bc95cad3186aea73d015557de9c43364e27ed98edd5a0d` |
| S10: classified; Part II, Item 3 | Item 3. Defaults Upon Senior Securities | 294–295 | `block:6ab68fee125d25167d9714dafba17dc82903eee7e36ba5456f2e94aa588b5748` | `block:77e8a43b4804552362d783738d3ff27f356981992756fb598838ae4ab19a7ef3` |
| S11: classified; Part II, Item 4 | Item 4. Mine Safety Disclosures | 296–298 | `block:c7e886721af2194b0cfa415a647cee9317023dd2b8895cbf42bc96b22a365442` | `block:19c5eb21a50c674c671f4df872bf78189385acbfc2f77053c746a47012b7cd09` |
| S12: classified; Part II, Item 5 | Item 5. Other Information | 299–302 | `block:7d1cfc5561f798c339a6b14eab4a2fc98eb807c6f569879f9edfff415f2fbfd6` | `block:2e33b77c4ce89752c82bdcb0d8b6c09be005fdffc066903313439669d9a98c6e` |
| S13: classified; Part II, Item 6 | Item 6. Exhibits | 303–307 | `block:933cafc6787a76d46f54d5355a949cf57dc8d0b0776ced2ace1d8d950416d046` | `block:595c0a7f1a4cec0dd0f7d7a00bd62d4683d5a252e41aaa5bf53c8f17dc1f1eac` |
| S14: unclassified; Part unknown, Item none | SIGNATURE | 308–311 | `block:dfc8385a9cce53ffa9eedda22ce568f7b26f5d449b2de2b4c163bb053fb0417f` | `block:d2d3d8d2fd6d597583813c81b96e6fb421b719095e0aaefaa1339d9fe82b12a4` |

### F08 — Microsoft — 0000950170-25-100235 — 10-K

- Filing date **2025-07-30**; report date **2025-06-30**; split **development**; **1,401 blocks**, **29 detected ranges** (23 classified, 0 ambiguous, 6 unclassified).
- Document ID: `document:011f513a22ff4c7d01d4d87e034b08787d9a778ad7a5d7cde1c5d0997367794d`.
- Source: [msft-20250630.htm](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/bd/bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665); 8,158,173 bytes; SHA-256 `bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665`.
- Logical output SHA-256: `b4fbe6a9f03885672cba5a611ba4d0e0de74842951c006f0d6666daaa022e963`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **1,401/1,401** locators; fetch `15292a04-83fe-4dee-a86c-38f5ad9b0781`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): none.
- Unclassified/ambiguous ranges: S0 0–32 (unclassified; Part unknown, Item none); S1 33–37 (unclassified; Part I, Item none); S9 486–488 (unclassified; Part II, Item none); S19 1335–1335 (unclassified; Part III, Item none); S25 1352–1354 (unclassified; Part IV, Item none); S28 1395–1400 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×4, `non_item_section` ×1; total **8**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | UNITED STATES | 0–32 | `block:5c920cb1a109f8f305918febf1205b97d551da46d815fef0fcadb13dae134b7d` | `block:fcebedab462f40bf4b41e9ffe4a524cfc67ae8ff693143a5db3cfb933e421c66` |
| S1: unclassified; Part I, Item none | PART I | 33–37 | `block:e9137599bb6d26bfba9a00afb5145870b3d4ffce2b9f400aae8edf7a840f9f64` | `block:652b784aa2098e80cd374566dda244bc9dacec5d9a30af4315d61c63e1d19e09` |
| S2: classified; Part I, Item 1 | ITEM 1. BUSINESS | 38–284 | `block:5e9c10ebb4d0f9a98d70182da242028fee73feeb932427ebef5d0ea6962fdaef` | `block:03f62ee9beb91a467514a697668de817ac6c578fae3218baf257a1935ae4eee7` |
| S3: classified; Part I, Item 1A | ITEM 1A. RISK FACTORS | 285–448 | `block:60ec0a8cc5a01879719f9c15db17511a502c85804edc5d9284c2abbb8722f950` | `block:963407fb548a821693832f553625edd9f646f405ea2c1fabfa8d96a3f90e6826` |
| S4: classified; Part I, Item 1B | ITEM 1B. UNRESOLVED STAFF COMMENTS | 449–450 | `block:c06ac7aaea3bc6ff8f4ade2991d5af0fd7e936cc8cbfd4b6758d1f81f6288071` | `block:b6000a9987358ba73db93a0434d27b8782b08e9e9fa9faf8f3e2004c02aa67df` |
| S5: classified; Part I, Item 1C | ITEM 1C. CYBERSECURITY | 451–475 | `block:4ba83cb64e8a498638094d480993cf10a0cdeeaf2834b01e68dbbd5b54d32c55` | `block:16c9516e71d03f0999f050205ae2b344a29c28441efa3bbf1915fe8310090581` |
| S6: classified; Part I, Item 2 | ITEM 2. PROPERTIES | 476–480 | `block:a392469834a323674cd8d6cddf00dd7228d3e6262fe69a268df23c18065569a8` | `block:f0b6761f873e9384215de5762cccce6f565e2971f26e21d882f564951a486f15` |
| S7: classified; Part I, Item 3 | ITEM 3. LEGAL PROCEEDINGS | 481–482 | `block:f8f23adf62601a586cc3d559750df50e662cac3e0b86d72928e8f1605db2733c` | `block:a1057652762d01b45b34f2b915c641c7bac51d6dfc2ffb70285040d5fce25c06` |
| S8: classified; Part I, Item 4 | ITEM 4. MINE SAFETY DISCLOSURES | 483–485 | `block:b30fd7e2522ebb9ecc5a15da005e7b8b7c415f7c14e01199e121c81a07305ac9` | `block:fd83967cdb601522b8a51549f16eb5c39843001231f82b35f83bc2108ca8bbe4` |
| S9: unclassified; Part II, Item none | PART II | 486–488 | `block:9970cc2c0b1a328584612a3e27a37cbaa24967e2daf37195b9fab3506413da79` | `block:40a923866b27b1ad42d77a7bd8de76bbfffe850e29f9b635ba290eeafbb226cc` |
| S10: classified; Part II, Item 5 | ITEM 5. MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS, AND ISSUER PURCHASES OF  […] | 489–504 | `block:a206f1458c48830e2607dca7597913ce733968dbb0d69179c7d91ef14efda6d8` | `block:b0c5f830390fc748568250ad417cd3531009ec789861012279a2db223af12fc8` |
| S11: classified; Part II, Item 6 | ITEM 6. [RESERVED] | 505–508 | `block:59e2bb4ef8bd26846890dcaad8ca5452425268a9ebededb0eae98477d4900337` | `block:24d8b308ec78b5523e348a0253d44d5a81c16b9be0c6d7a473ee6bfc35d45ce4` |
| S12: classified; Part II, Item 7 | ITEM 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS | 509–760 | `block:ffd5fb7842b35a41a7daadf73824a9be54859d0192605016d6e0a5a4c6513029` | `block:4ba770ee50a87d2d625ee471db8188e7fab827b8990223036ce34bc8b3acd566` |
| S13: classified; Part II, Item 7A | ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK | 761–777 | `block:cd60203953acf7fba3eaa9349b522f530a76634cdf557f40cd2ef648f6957aac` | `block:3834fc876dee99bd1ec7d1003b4cde1000680508ed4da6fdf3a4c7116e311e6e` |
| S14: classified; Part II, Item 8 | ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA | 778–1302 | `block:0a1e4cbb68b0b11edbf144a361c376664791fd0b79276c6ec6d003b3fbe265aa` | `block:0b292af5a4c526e911eafd06efe1726ba37febfc66cd8627ba7eeef461bef12d` |
| S15: classified; Part II, Item 9 | ITEM 9. CHANGES IN AND DISAGREEMENTS WITH ACCOUNTANTS ON ACCOUNTING AND FINANCIAL DISCLOSURE | 1303–1304 | `block:b8d63c7a263d9be9f91ba7f126012577c555ae9fd614d35bd3b642b02e0e9a5c` | `block:ae7ca859a17264e725f12b8430df45d25d43cd5dd986500d52a7e7f85cdc2103` |
| S16: classified; Part II, Item 9A | ITEM 9A. CONTROLS AND PROCEDURES | 1305–1329 | `block:021a8fd187b01734aa2f2aa89bdf0f2be42f8ff2eef20759af0c7a2da9cfc10b` | `block:c553952e6de07c1dcb4805666488712053c11f965eaf4473b09a6baec7bfe1e4` |
| S17: classified; Part II, Item 9B | ITEM 9B. OTHER INFORMATION | 1330–1332 | `block:7d20f38be61199b8ac876fd67c9d1f9501ca7985e1248b131706056db3050b90` | `block:dc0dddae872d1b56e5068b02ef9434538491af01d3e2f684c26e1af4778830dd` |
| S18: classified; Part II, Item 9C | ITEM 9C. DISCLOSURE REGARDING FOREIGN JURISDICTIONS THAT PREVENT INSPECTIONS | 1333–1334 | `block:0463bd742ea98ba0f63b814754c12370e096926415edb463d45c65344bc4f61e` | `block:9ca17da73e3f9f4357394e53505869c56f52a932ccb6b62f40a5ec61b3322ad4` |
| S19: unclassified; Part III, Item none | PART III | 1335–1335 | `block:bedba56bf71177a72dd7cd0237373b6bb07fbd0be8c0e3ffdb1a99f6a26a7cdd` | `block:bedba56bf71177a72dd7cd0237373b6bb07fbd0be8c0e3ffdb1a99f6a26a7cdd` |
| S20: classified; Part III, Item 10 | ITEM 10. DIRECTORS, EXECUTIVE OFFICERS, AND CORPORATE GOVERNANCE | 1336–1339 | `block:303f8e97584aec50a856f061672145456fe46b0b6a3059fef3fd979622590c8c` | `block:9c657437b4f5fcb4da0ed997c2f9149dd95b3809bfc22f30b1c9d0a52a5edc5a` |
| S21: classified; Part III, Item 11 | ITEM 11. EXECUTIVE COMPENSATION | 1340–1341 | `block:bb750a18f7d0a91564cb2b6502022c54c83a29b2833108992be96d696f29d688` | `block:2c32f26a2f06a67c34314e962259098895106905bbdee0a7adf2d16eda932580` |
| S22: classified; Part III, Item 12 | ITEM 12. SECURITY OWNERSHIP OF CERTAIN BENEFICIAL OWNERS AND MANAGEMENT AND RELATED STOCKHOLDER MATT […] | 1342–1343 | `block:3efa7062e24dbfe8a1cc0874b7b1260c1a1fd7309530f094f51c7cc83e9f6527` | `block:78cb5a181712a11cd351b5cd452bafe2f11ea4923f798a0c4d53b9519b3be4d5` |
| S23: classified; Part III, Item 13 | ITEM 13. CERTAIN RELATIONSHIPS AND RELATED TRANSACTIONS, AND DIRECTOR INDEPENDENCE | 1344–1348 | `block:e00ec7a0f2d66f8160d9a3ca128af233f81c3ef10c0ed2312cb4de3cffe4c235` | `block:ba09f6bc8d8f551561efa7e068f595f812b7ea311d1b82046957cfb98f11c338` |
| S24: classified; Part III, Item 14 | ITEM 14. PRINCIPAL ACCOUNTANT FEES AND SERVICES | 1349–1351 | `block:ab436b4f006499b7ca6c7b6e190c3645c26facbc367840971966adcde4beb432` | `block:4b5898c4ad63932ace9cdeb3b58d7e4ac94a4179017daf959d5da8af1f820193` |
| S25: unclassified; Part IV, Item none | PART IV | 1352–1354 | `block:3e31738ff24fe13cb81c888a042d209ae19769260644357c2d25133d9a7eb10b` | `block:7c0d19c17d5ca06c457dcec13fb1fd37301f02a2e64334c62d649bbe653e7c00` |
| S26: classified; Part IV, Item 15 | ITEM 15. EXHIBIT AND FINANCIAL STATEMENT SCHEDULES | 1355–1391 | `block:30c14a8495b263b142ccfd2b457d4fbb32c786a398826ae710fbdde324a661a3` | `block:a1b6f2e4ab28b9ff1e046a7d17426cfd4c76778b40ae28ed7b544f0fd5b31bce` |
| S27: classified; Part IV, Item 16 | ITEM 16. FORM 10-K SUMMARY | 1392–1394 | `block:8513e624cd13d70858dca812722710a2e352bf5b17e09e882e238d9dc2783da9` | `block:381839f0dff33470ea61eb8a4c5c958a074fa4e9e1e4b9f4c98226b8affa9626` |
| S28: unclassified; Part unknown, Item none | SIGNATURES | 1395–1400 | `block:80aa60f9057a0ee428c532319cdda76ad88d2ae8292d4c4563730a80ab0e0739` | `block:160f8a93703e77ab03a33a005d25b00ae0a720822d04c7c68af331afd9422510` |

### F09 — Microsoft — 0001193125-26-323660 — 10-K

- Filing date **2026-07-29**; report date **2026-06-30**; split **held_out**; **1,401 blocks**, **29 detected ranges** (23 classified, 0 ambiguous, 6 unclassified).
- Document ID: `document:e1be24bc48e26775e8f9ad3c0dcbe62839b51355fd44ab760d8e243e0879a606`.
- Source: [msft-20260630.htm](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/7e/7ee403cf6248837b88b69729c38534d60f1171fd1447ba0fa3ac426abf2430cd); 8,585,607 bytes; SHA-256 `7ee403cf6248837b88b69729c38534d60f1171fd1447ba0fa3ac426abf2430cd`.
- Logical output SHA-256: `eb20bcc348906bfa9fba88b8c33fa46087646539627a6418d515f99f4f767cb3`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **1,401/1,401** locators; fetch `a873e582-8326-45cf-b48a-e785ae760ccf`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): none.
- Unclassified/ambiguous ranges: S0 0–32 (unclassified; Part unknown, Item none); S1 33–37 (unclassified; Part I, Item none); S9 471–473 (unclassified; Part II, Item none); S19 1335–1335 (unclassified; Part III, Item none); S25 1352–1354 (unclassified; Part IV, Item none); S28 1395–1400 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×4, `non_item_section` ×1; total **8**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | UNITED STATES | 0–32 | `block:27ae2889b354a6b549992d8feb9d9a51372bb7c365fedaf53482886a3b8c92e2` | `block:a6abb11e8d04cfb340dd2eab6753c4f29e11cf6e1ee536ef1d015ea644bae81f` |
| S1: unclassified; Part I, Item none | PART I | 33–37 | `block:b06460a60b45cdc087650738b90b6e807ac9b966e4f94e07fb6ec092a750fc44` | `block:c4e14ce5d96a643e326b434eeb183ecb0f319d971755590a3c536165b464f7e4` |
| S2: classified; Part I, Item 1 | ITEM 1. BUSINESS | 38–254 | `block:b063dad4fbb761c5a3a79c27f8c9db2719694b9f17d216f84aa6d1710c8e587d` | `block:1e83523a0e707531ee345deb38044bd067bfc01bbc5035b560214d23b7da2747` |
| S3: classified; Part I, Item 1A | ITEM 1A. RISK FACTORS | 255–439 | `block:d32fe9ae8c5007fc017167e2ad7e7d3c6d506cce10e43a9afdad807621e806c3` | `block:ed1f3ff0a5deb0a95c471268d5f48c5ee371b4f77ce1a1a3dbc078a59ef0cf3b` |
| S4: classified; Part I, Item 1B | ITEM 1B. UNRESOLVED STAFF COMMENTS | 440–441 | `block:4a1fd0bef0c365c8007967c781007119e59f74534eb80bd57b48ce8e538771d7` | `block:bdd9d0ca5e0f1ee7f5a323e64f09c41d01e9890bc8992c05523b4fd8e598abc6` |
| S5: classified; Part I, Item 1C | ITEM 1C. CYBERSECURITY | 442–460 | `block:1d0a64e65b43f2dfdab20d5f44c89e763936b6845247a415cdd53bf6eb98bba4` | `block:eeb2d26dca390ecdfe1adb52962a3519a74f2af67e340690ba35b0ddce7ed0a1` |
| S6: classified; Part I, Item 2 | ITEM 2. PROPERTIES | 461–465 | `block:6c3b0c2eb1bcdecf9025e5edf22629c95aafe344fd53a51f00a2d9b8d61bb7a8` | `block:09d3be54c16dbc4ccad061222cac25a89114918c0e423395120ad4f9a8714d7e` |
| S7: classified; Part I, Item 3 | ITEM 3. LEGAL PROCEEDINGS | 466–467 | `block:2e4cdc116ec32819c09ddf01e602586baf9d545dbe7ac3bb22e4771ec3f4f01e` | `block:0b6b453a112492e8c6641387f63f0ed359b99835b3a7617b3f8663c956ec4ea0` |
| S8: classified; Part I, Item 4 | ITEM 4. MINE SAFETY DISCLOSURES | 468–470 | `block:dbacf7436b8c19e456f51133f15b6881d6bdaac4c01ba27d91f510147ce67974` | `block:9d0d7126edb13cea8a639176cd337cb52e65cb7695b4d8e7502f64decb6906dc` |
| S9: unclassified; Part II, Item none | PART II | 471–473 | `block:176ab3b63f3982c4aac0b5559dee074b1aae4e7d0afae53c3a2e9a1800b609a2` | `block:a548928e21b3ca9b2dd990eea9b77efc3e96d4ca1244ae7c0831b596f070ca82` |
| S10: classified; Part II, Item 5 | ITEM 5. MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS, AND ISSUER PURCHASES OF  […] | 474–486 | `block:c3f040a885f2a50277f39192b0169590910b3c7d924d4f8362fdf734f26bde20` | `block:4d7ecd03c85f44bdebe96369c7d823141f84212e8890359b990814c8a30918c2` |
| S11: classified; Part II, Item 6 | ITEM 6. [RESERVED] | 487–490 | `block:0171f7303812ef77b409151eb33df29153abc465a91223ad771431000634d1f8` | `block:d7c72e59cfb53084611c0f1b47e1f17a0ea82322c614bc261524d5f672e48239` |
| S12: classified; Part II, Item 7 | ITEM 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS | 491–755 | `block:eeca5dce6716da548b5c1589cce3a40ff7f2a18637cd0cdd27b3db244c5bf976` | `block:9594f928a6eb3d21a915aea6c7b419894b7eeec33e3415a65444f6eb6fa43ace` |
| S13: classified; Part II, Item 7A | ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK | 756–772 | `block:a0a3af9cc204b9636f3f13c12f4de49de23f323a22a3a8174d04384c214999c5` | `block:1c50dc22658fdb3c570862621b972fcd49a1689def3c0a98b468c3631e982c1c` |
| S14: classified; Part II, Item 8 | ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA | 773–1299 | `block:735a68addbf727f5a4045ec63bd01a101349e888605b2e64122ccc9d56d50b35` | `block:d437c515f1fd3e300bb18b55c296c35e42608c86d5eb43408462e76849f7b2aa` |
| S15: classified; Part II, Item 9 | ITEM 9. CHANGES IN AND DISAGREEMENTS WITH ACCOUNTANTS ON ACCOUNTING AND FINANCIAL DISCLOSURE | 1300–1301 | `block:1475816f1ecfbcbfeab49cc1f1f6bf646d0cf159de951f51384cf81f85ab107a` | `block:5424d9f696a3b56fcfd68a018e5cb72020b968992d240d8f42dbe266a3a3367f` |
| S16: classified; Part II, Item 9A | ITEM 9A. CONTROLS AND PROCEDURES | 1302–1326 | `block:a2257871d713685befd1d8e0662fca71ba483a66d8d70268df49d515cae8fb07` | `block:8ad5fa1aac261ede166b13a2cb810ab24dd8feef0a5277368912cc2a0f58bc8c` |
| S17: classified; Part II, Item 9B | ITEM 9B. OTHER INFORMATION | 1327–1332 | `block:86b0a6381308a3d8820cd76e1c198ddf1985d2374bfeddce725594a96d140deb` | `block:e7bf002899be17a6e5398731017837393b2e4d004ad39f97e0c6b43531870fd8` |
| S18: classified; Part II, Item 9C | ITEM 9C. DISCLOSURE REGARDING FOREIGN JURISDICTIONS THAT PREVENT INSPECTIONS | 1333–1334 | `block:cfa801d63cca722d29c6c37620d93bd0b6e99a40f68ab4e61b38cdb6b00747f3` | `block:b99f3fe032780c8e5a7bd72bf2911a6a91774c5ae4a861e9d8ffeec5c68f9921` |
| S19: unclassified; Part III, Item none | PART III | 1335–1335 | `block:55ab1c47ec95e68cc8c4941341f06cabdb28fd42f20da4479a2b35ae4209327e` | `block:55ab1c47ec95e68cc8c4941341f06cabdb28fd42f20da4479a2b35ae4209327e` |
| S20: classified; Part III, Item 10 | ITEM 10. DIRECTORS, EXECUTIVE OFFICERS, AND CORPORATE GOVERNANCE | 1336–1339 | `block:52d04c6ca5de15c9684010fde8594cfd738182372171151e5ee121d37c79805c` | `block:a3ff5229d8dd037bc411f4f2d1b31e73244b8c5831349a375582ded131bd90e6` |
| S21: classified; Part III, Item 11 | ITEM 11. EXECUTIVE COMPENSATION | 1340–1344 | `block:7dd92d8398411e383fa4b45e23cb609eed960822544615425d54e20fc161ebb8` | `block:9ec5c7b2efd1b7368b28f676c0f4b3d8f17dbc2bedfac49cda2daaee0a260445` |
| S22: classified; Part III, Item 12 | ITEM 12. SECURITY OWNERSHIP OF CERTAIN BENEFICIAL OWNERS AND MANAGEMENT AND RELATED STOCKHOLDER MATT […] | 1345–1346 | `block:bf986182a0327cfb35aef1a0a0dec8f5eeb6365556bdc88adc7f6c210d08b1ff` | `block:c71694e3bdec045365ff05865e9d3673d8aa1bf47dab991fa5bb4e1b12269673` |
| S23: classified; Part III, Item 13 | ITEM 13. CERTAIN RELATIONSHIPS AND RELATED TRANSACTIONS, AND DIRECTOR INDEPENDENCE | 1347–1348 | `block:bf089ee7013522ac2a0055faba20bf9546e3362147d508e140be564f1077f63b` | `block:abbd7c344ebcf6bbb80ab0bf1682060b94bc107884013c4c120c58411a0b3a0e` |
| S24: classified; Part III, Item 14 | ITEM 14. PRINCIPAL ACCOUNTANT FEES AND SERVICES | 1349–1351 | `block:9ebd8686f6ffae1589a258f7b15f63d09c13cfde08c7cbf2eef8ced98fd3e3f8` | `block:40b982671f9182a3b56302b9d72cc804c7a23990a587c6fb80195d61a80881de` |
| S25: unclassified; Part IV, Item none | PART IV | 1352–1354 | `block:3b83dde2c8c239854bff5a3ef35b0ea580ec5ff8f4ee4754db08cb9e5ae41dd4` | `block:33bc0ec2630cba49e198fd2204e6ce4b1baad9375bd2caa1fb89affd6a93c028` |
| S26: classified; Part IV, Item 15 | ITEM 15. EXHIBIT AND FINANCIAL STATEMENT SCHEDULES | 1355–1391 | `block:822cee075a72b433439f916b950dd85a7baf5bb8d088727c8612ebbe31d47952` | `block:4c706ec049aca81b7b9fa6a9198528aaedee235957efad17520dcc18d5cb94cf` |
| S27: classified; Part IV, Item 16 | ITEM 16. FORM 10-K SUMMARY | 1392–1394 | `block:e2a9cf194e39b2b536bca1f53e26cea413338adbd3b1fd1311d1514422f263cb` | `block:9ca48bfc4b8a1b05e877eeea561985efcd3d83c88d692d36c3d3951dd7005857` |
| S28: unclassified; Part unknown, Item none | SIGNATURES | 1395–1400 | `block:6a40f041198ae04c158233aff152ea2839689b3142a1297db62e1335408e5db2` | `block:07b5d3890a4b9798e97e5b23a1616fec86e4496f2f2e07dcabc8720e557422ef` |

### F10 — Microsoft — 0001193125-26-027207 — 10-Q

- Filing date **2026-01-28**; report date **2025-12-31**; split **development**; **881 blocks**, **13 detected ranges** (9 classified, 0 ambiguous, 4 unclassified).
- Document ID: `document:ea322da70fcd6fd0e69ab7f893f045d092e2c423e108ac64d1d505da38d96ca6`.
- Source: [msft-20251231.htm](https://www.sec.gov/Archives/edgar/data/789019/000119312526027207/msft-20251231.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/13/13b6006248fb7d5f3dfebb5425e6645a8ca4f8e1a438fe1c75a0578be13b2773); 7,483,384 bytes; SHA-256 `13b6006248fb7d5f3dfebb5425e6645a8ca4f8e1a438fe1c75a0578be13b2773`.
- Logical output SHA-256: `7803c684d46b1b55700e52ec8bed8213408023563d1f42b2c6e8cae21800d43a`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **881/881** locators; fetch `ad933e1f-7e53-4243-a574-65e092d1f680`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): II:3, II:4.
- Unclassified/ambiguous ranges: S0 0–25 (unclassified; Part unknown, Item none); S1 26–28 (unclassified; Part I, Item none); S6 680–682 (unclassified; Part II, Item none); S12 877–880 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×2, `non_item_section` ×1; total **6**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | UNITED STATES | 0–25 | `block:b63935dbe0333202938709b79b1aad8fba65b35c4ae3711f69601bfdaa7b5374` | `block:5bb4adb0af72c88d07ed3e2bba9f72566e5c128a2f2e6c08ffef78a4a69bbc80` |
| S1: unclassified; Part I, Item none | PART I | 26–28 | `block:470cdd90fa9eac966d24ef568c30563d422849e8ba32bdae9f2d1c45662608a7` | `block:28efa439a3a881313c9cb12a76b1b3a8039d96e8971c1a705dc9eeb6aad3b7d3` |
| S2: classified; Part I, Item 1 | ITEM 1. FINANCIAL STATEMENTS | 29–344 | `block:334e71455f195af60eec77682b89dfc2397300ffd42883630daabb45cf2589d4` | `block:c4fbc1b687c7f8b9ce229e18bf8fd3b4a725624f92f18b4c9122c43f9533cdcd` |
| S3: classified; Part I, Item 2 | ITEM 2. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS | 345–662 | `block:b5006d8a8aabb39ca5a71f90ce68bcfbf33b5228b88f0da498bed2dbe484aba1` | `block:aca98f9a9ea634a1b77e82d4ae15c672e9a26169859c9ec531554d1b684f978d` |
| S4: classified; Part I, Item 3 | ITEM 3. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK | 663–676 | `block:6ee210405d68d7bf9586afa6296782a3430e903205bbd3f562bff3ba63b2219c` | `block:a7bb62440e9301619e8d20a96405954fe63b9edb960764148f3869f24309dffa` |
| S5: classified; Part I, Item 4 | ITEM 4. CONTROLS AND PROCEDURES | 677–679 | `block:627554f54292642620e413016871fd7e2b37741a94f03bc34803ba45390718b3` | `block:81b8d028d806d7ecc26fa6ed5016fcb55ae00eb9c00fe7d445560e4a45dce15e` |
| S6: unclassified; Part II, Item none | PART II | 680–682 | `block:5c721279ce9474b62946d6f57fa70a75a4ba5c20a43cc31d7e5bbd2349a1d7ce` | `block:81034c635c2bd5f5f056fa685d90b2f60264cc7937cc1898d07285a71414b9ca` |
| S7: classified; Part II, Item 1 | ITEM 1. LEGAL PROCEEDINGS | 683–684 | `block:d9f67c91407dc91d845d3d512b907bd9a035cd7c3cc2ab49f558c987567159ce` | `block:e6f81fcfb69f7f4b89ba321914982bcdb755b71defcb6fef7c075ebd15e2c44b` |
| S8: classified; Part II, Item 1A | ITEM 1A. RISK FACTORS | 685–852 | `block:8004aab7c82f5a2cd5d6105f68b394d9f67084c6b96d53968d5f4a8933237627` | `block:9eebba4d4998f7c1be8906dabe7e9c7028d7d2d84001dc18bef4d7f86699a27f` |
| S9: classified; Part II, Item 2 | ITEM 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS | 853–863 | `block:a57d09355cd758deea359db65e26495316959fcd584d9660ac59726d11cd3b8e` | `block:c66f3b347ab47eeadc9e7cbdf2fe424bcab6f4acc46495ebda55b5ab4bc0df9d` |
| S10: classified; Part II, Item 5 | ITEM 5. OTHER INFORMATION | 864–871 | `block:309b27fa325b0dbd4cc8fdfe4e4f0b29580d9f21418d2b9ecaf6146fa3102695` | `block:2a9d463d3930e582614ea6e34bf6e622b2b05a18078fec3d166db1eb866091a3` |
| S11: classified; Part II, Item 6 | ITEM 6. EXHIBITS | 872–876 | `block:3405853ffd1dd4c6e30b45b63fb6414d9efda11426380d4da92f8babdc809017` | `block:ea36ab56bdf429bf8f8565f3822d5ab4c3fb1e5b9cb0893332f880e12afb9fa0` |
| S12: unclassified; Part unknown, Item none | SIGNATURE | 877–880 | `block:2f7e88b31e5c70d3189ef29a9be14e7da01453dfac1c5cf90e497812116e6ffc` | `block:036eae6a5d314f3515c7bbdd4a76a41d581909af275a6fa9294d7a060636e904` |

### F11 — Microsoft — 0001193125-26-191507 — 10-Q

- Filing date **2026-04-29**; report date **2026-03-31**; split **held_out**; **894 blocks**, **13 detected ranges** (9 classified, 0 ambiguous, 4 unclassified).
- Document ID: `document:919e86532aa8acd130f979412da824e4590170b8ac3ce2142e44021575166fdb`.
- Source: [msft-20260331.htm](https://www.sec.gov/Archives/edgar/data/789019/000119312526191507/msft-20260331.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/f6/f67faa481eee34adcbd34f779d92f85ee357ad934ef9a5b9ffa43ce2522027f1); 7,732,054 bytes; SHA-256 `f67faa481eee34adcbd34f779d92f85ee357ad934ef9a5b9ffa43ce2522027f1`.
- Logical output SHA-256: `8cd7a2ae38d80c188aa2d95e94d8bc873855861e58c1df36f2a5576cc6b6c85e`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **894/894** locators; fetch `49f07a99-64df-493e-9881-519aff2ad6fc`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): II:3, II:4.
- Unclassified/ambiguous ranges: S0 0–25 (unclassified; Part unknown, Item none); S1 26–28 (unclassified; Part I, Item none); S6 688–690 (unclassified; Part II, Item none); S12 890–893 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×2, `non_item_section` ×1; total **6**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | UNITED STATES | 0–25 | `block:b41ca6f8063802378a477586fd28ff670de52e69777d5b38988de7988d63674a` | `block:3e21ba63cfaa77a58f23642a9ae7ceca83a2eeb570f6eba6f2b5b6c6ea99c979` |
| S1: unclassified; Part I, Item none | PART I | 26–28 | `block:db917ec9432554f5cee74eb2f13f90fb04603a7f94de023d41a60293cf101bfb` | `block:ef5d2f73f202f137596b0cd394f49d1c44906d928dc0793db418021bad5e2368` |
| S2: classified; Part I, Item 1 | ITEM 1. FINANCIAL STATEMENTS | 29–347 | `block:1fe53a90b7ac1077d2ea4e9e8a6189e2719fd6565f105c3c5acc25c65a85ab33` | `block:fa866d579b356086e3cd2c7be69d76f1c456e7fdba5eeac85efaa335d7bcc625` |
| S3: classified; Part I, Item 2 | ITEM 2. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS | 348–670 | `block:fa415dbbee9ccdfbc4b87c98bd064300a5b6cb53167371c92eded4d7076fbb51` | `block:65096e0547b1a971606288e74678dda465386a28882945aebcf4fb5aee89806e` |
| S4: classified; Part I, Item 3 | ITEM 3. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK | 671–684 | `block:0f770018efc473669397735d4082e986e0021274c1427f9166cf897ba0b6897d` | `block:907a5c0f2954d41effa4d6ba2b04df3fc01981fc9ac97fcba107782d4aeb4289` |
| S5: classified; Part I, Item 4 | ITEM 4. CONTROLS AND PROCEDURES | 685–687 | `block:982b8eafacb29a4cc8c28ebe07de01b234b2ed6f1ebb3e878cc9048b10f66e07` | `block:a0209252f83d93d0d3e67cafd82840e81c7117d5a27da1c9d49eb83b7a78a8f6` |
| S6: unclassified; Part II, Item none | PART II | 688–690 | `block:86ae704666d224cdd9fefa6378de5a060bfa0172498f0b5c468596b75bd65bab` | `block:cd6bfa0dc69eb20e42684881ae076606956c27b7ed4a4c8193071c666901f56c` |
| S7: classified; Part II, Item 1 | ITEM 1. LEGAL PROCEEDINGS | 691–692 | `block:7ab1d5c8b21ec62c48bb33c6d63e6204ad94648af4fcc043e05c79a45dc74dc0` | `block:33fab85edf2ce5a3c0f375b03ad9a5fe232053e53f8cec1d1eb956b6290776a5` |
| S8: classified; Part II, Item 1A | ITEM 1A. RISK FACTORS | 693–863 | `block:8a87b32a916d350b5d7f2bac49e195e2b82d61c314dca5a16b5c3253c3090713` | `block:e9a4c23bef578893117646fa1c4acb880716bb2da5c16b021fe8690b7d647a0a` |
| S9: classified; Part II, Item 2 | ITEM 2. UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS | 864–874 | `block:3ff50e752122012fe325f40cd796ba867aa899041106f2694948e9047dc8fadc` | `block:c7537a72baf67312c10632fc557bb6bd79efe432b80873df499fbc6a705674ff` |
| S10: classified; Part II, Item 5 | ITEM 5. OTHER INFORMATION | 875–883 | `block:b9496199d46533a201349a53e25c7e9e4bf2bf691d307884556f884e164e11e2` | `block:1573ab7c054a2380373ac9185dd886edba9b8d16951cbea0602fa25e4e37fe80` |
| S11: classified; Part II, Item 6 | ITEM 6. EXHIBITS | 884–889 | `block:9b67b77fe3de89a4102b0ff6f0d50571bd2eac479afa570d3b7d3b8bee34b75c` | `block:be1adc6fcc1acb5302a7e6dd6e8abecd8b9e4e986d52d288895c7a58ab4cf97d` |
| S12: unclassified; Part unknown, Item none | SIGNATURE | 890–893 | `block:f8ac00c57e72361f7c4c55b1b253527d4876ccb48f85260eadc9cb756ffbf0e4` | `block:89d3c324b2eb6bcc4cec600323e6778a102a90a3833e57f946a375bff8e8c198` |

### F12 — Amazon — 0001018724-26-000004 — 10-K

- Filing date **2026-02-06**; report date **2025-12-31**; split **development**; **1,017 blocks**, **29 detected ranges** (23 classified, 0 ambiguous, 6 unclassified).
- Document ID: `document:a938656a32a3ca28b99ce173af41ad362350fd609215aec8b61fc2e8f1d548e8`.
- Source: [amzn-20251231.htm](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/a2/a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35); 1,968,448 bytes; SHA-256 `a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35`.
- Logical output SHA-256: `aed9509cdb608e929b844f308a370cf464d0f7444169ade439e730fce4f7a6a5`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **1,017/1,017** locators; fetch `05f7a6bf-d034-4f54-b00d-7364dc9fa4d2`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): none.
- Unclassified/ambiguous ranges: S0 0–52 (unclassified; Part unknown, Item none); S1 53–53 (unclassified; Part I, Item none); S9 298–298 (unclassified; Part II, Item none); S19 966–966 (unclassified; Part III, Item none); S25 981–981 (unclassified; Part IV, Item none); S28 1011–1016 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×4, `non_item_section` ×1; total **8**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | Table of Contents | 0–52 | `block:a1cc7997ef7b432077dfbeeaee70000db1ee6ae02f3e9ce6e6a7de07245fe04a` | `block:b6e21e4efa8393da0936d984f24e1bd335dc430fe9789fe4b23ec73a9b31a451` |
| S1: unclassified; Part I, Item none | PART I | 53–53 | `block:7c6a275532f6ff17ae160669da960a9c509af37fc17cce68eaf8b73ba43cda8e` | `block:7c6a275532f6ff17ae160669da960a9c509af37fc17cce68eaf8b73ba43cda8e` |
| S2: classified; Part I, Item 1 | Item 1. Business | 54–99 | `block:d86e45cb07839b502658b5d065132611aa1ceffca686a3882e8bdd7b5d4dd23a` | `block:7b57722b7750dae7bfe09d11cf4fda6c067c69b0bfba7184924c24b5645304d8` |
| S3: classified; Part I, Item 1A | Item 1A. Risk Factors | 100–270 | `block:69673055da749dde4eaac3389afdd0f9c9089a4200bec48af6131c6eedfd8a44` | `block:1e39942fc0feccbee34c6b48eaec1b996c0f1612527a861b3d15ba7bc4c41823` |
| S4: classified; Part I, Item 1B | Item 1B. Unresolved Staff Comments | 271–272 | `block:02f3d675d447a2f74c5095e4c7436e4d4035d6487b45072c8b2ce2b7c100e6ed` | `block:4ccced7f678276636fdef85fd815ebf6e45e545e22b04b0b149f208ca060a569` |
| S5: classified; Part I, Item 1C | Item 1C. Cybersecurity | 273–281 | `block:a24ad9a149693282bacad4b3506712c9d11ea730c7c58fe508f092783a99cb15` | `block:47e9eb6423432681ad5f6df9b6ec2cc91427cb08f77d5ef7529ae318d67ffbf7` |
| S6: classified; Part I, Item 2 | Item 2. Properties | 282–291 | `block:246952c7ba5da8eaf333165d9ddead5c4ce28b6916df56f1013788e50368e4a8` | `block:c29a8ec9965388e03eda0d041f7e52190a3ecf9d42f2cc5282dd66daba14a046` |
| S7: classified; Part I, Item 3 | Item 3. Legal Proceedings | 292–293 | `block:725a79621d340db1f0015e9c10c81c2b73c946bd3a82925f1f275e37d64801ab` | `block:52a14846816da48a57bd86e9d07cb089d35da1f35be625d4f123d3b47533e7a3` |
| S8: classified; Part I, Item 4 | Item 4. Mine Safety Disclosures | 294–297 | `block:c0ad378e8c8a11709b753e8ba9a4d8f48de1c042ef675744615c5fb03214c6f5` | `block:0d5105b9394adaab22e3af93bbd208b164e3793331960f7ab56e998f7a7970ab` |
| S9: unclassified; Part II, Item none | PART II | 298–298 | `block:daf072d2ac682a9bc1c266c7a30f0607b49eebe85e90d11440854fcd62b6ee50` | `block:daf072d2ac682a9bc1c266c7a30f0607b49eebe85e90d11440854fcd62b6ee50` |
| S10: classified; Part II, Item 5 | Item 5. Market for the Registrant’s Common Stock, Related Shareholder Matters, and Issuer Purchases  […] | 299–307 | `block:a65d90596e43986d45f6b8d659ac2511a3d912812f470347bd9a389d4b8539a1` | `block:1db61bdb6747073e84b95ce36ce981279aa7b3c96736602fd4e1c398884ad744` |
| S11: classified; Part II, Item 6 | Item 6. Reserved | 308–310 | `block:e974e26b5da2c4ef85b77077d953166de0d5d2b9706682f66713712e47ee15e6` | `block:358b80fa32d0b26b606f4f03fb1c19f4d292b0d1995b46229dbd6b1f40704cf2` |
| S12: classified; Part II, Item 7 | Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations | 311–442 | `block:184849f27223ee9a416120e2c03fc7a4e76e9a9c227e8d0f500c7ac0b44c2282` | `block:a751a304d604d97fa503920f8e591bd35926d932fb504f44ac430303ff3ff69a` |
| S13: classified; Part II, Item 7A | Item 7A. Quantitative and Qualitative Disclosures About Market Risk | 443–460 | `block:d9dca22cb24c0be23bb104acc1d0a42c2e2250794ec3873fe813b9da0ec4919d` | `block:f79293ae57fa4122203b17021ad0419c4ded04bc6f108d5a904f9f1c4bd1fb02` |
| S14: classified; Part II, Item 8 | Item 8. Financial Statements and Supplementary Data | 461–924 | `block:d5d68a599da226849118681d7179db21c702d8ce38d02a148cebabbc67510575` | `block:a4b4fdc09398cd4a65cdc712c6b66bd41b050e49d6a6a99dd2fbccc2199740f3` |
| S15: classified; Part II, Item 9 | Item 9. Changes in and Disagreements with Accountants On Accounting and Financial Disclosure | 925–926 | `block:f790dece8fe90dec6fe7cf2c0162531b579bad8a521100829c9bdca1d0bfbb8d` | `block:38cef484f402bf252630f7065509ca9d714bc66aa8c20af7f08735a46d7c2d0f` |
| S16: classified; Part II, Item 9A | Item 9A. Controls and Procedures | 927–955 | `block:106b8b9dc70faf70296b68a2c1f7f351dce76a309dcfcf8e709c3b3ea62a0818` | `block:6bc889672c13dfc4df02858438fdd2f1ecb4de9f4d29ffefe9e078007bd79923` |
| S17: classified; Part II, Item 9B | Item 9B. Other Information | 956–963 | `block:9b1328a13d18f1d54fe609ea8ea98fdfaa25eadd426ffea599ca1480b4420625` | `block:2fea87aaa9e0a5d260cdc669d7eebec56c15fa278742bc6c7c2fa2d46a0ef6c2` |
| S18: classified; Part II, Item 9C | Item 9C. Disclosure Regarding Foreign Jurisdictions that Prevent Inspections | 964–965 | `block:b54a8f0e30acb4a31bc6fa2adad4fbd577a05e65b5d288ac6ce84ba6ba0641cf` | `block:1915a8c5787e24c625570795160e7674c75864bc0a50263460eb9f25fd619a91` |
| S19: unclassified; Part III, Item none | PART III | 966–966 | `block:7a6c933fd7b6420158739057fb8d5dfc7a50d84d3720cd4ee9dad03bf58d95b1` | `block:7a6c933fd7b6420158739057fb8d5dfc7a50d84d3720cd4ee9dad03bf58d95b1` |
| S20: classified; Part III, Item 10 | Item 10. Directors, Executive Officers, and Corporate Governance | 967–968 | `block:6d0fc85d1904395dcd9b3e73f9a9b58ce7c0bc8ded8fdbd50d474d78b424e0c2` | `block:16c198481dfe5ffcb9847fac07e4afba285561037d3a75b5e7bcad145d1227cc` |
| S21: classified; Part III, Item 11 | Item 11. Executive Compensation | 969–970 | `block:cb5a4f6937b39e92b25c864f08b9250af5a18359454649be474d0483763ea921` | `block:52ec0ff1dce31f9e707c1c654da16372fa7bdc129336c49846491c453a76b316` |
| S22: classified; Part III, Item 12 | Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Shareholder Matt […] | 971–974 | `block:7a0485487749433ccd8f2b96731cf04091c8356b2756fa51147ea53dd363261a` | `block:491ae50e310c40fd649992f1c0fc79d632f1533ec217fca742035480451f5a56` |
| S23: classified; Part III, Item 13 | Item 13. Certain Relationships and Related Transactions, and Director Independence | 975–976 | `block:a7f9e352ff9230497c6862e50d1f46031948bc6e275beff2bc6588d7f94f9b2a` | `block:a9ebd62cfbd4ab303e33d551ed9b1c2cd90bd79e057db5e8293fe560f1dc7ca0` |
| S24: classified; Part III, Item 14 | Item 14. Principal Accountant Fees and Services | 977–980 | `block:3d7c7efdb4ee070967289dbfdbd138714a95247f64b367ddfddf78e83f8867c4` | `block:e44d7e6a1b99905e9ba8490e1816afeb5b6d96444591df7a4299efd4350e1058` |
| S25: unclassified; Part IV, Item none | PART IV | 981–981 | `block:cdffdc4d82fae0d0b3f059e10efe2a793c92fb980cc5ee8980cdb864227435a9` | `block:cdffdc4d82fae0d0b3f059e10efe2a793c92fb980cc5ee8980cdb864227435a9` |
| S26: classified; Part IV, Item 15 | Item 15. Exhibits, Financial Statement Schedules | 982–1006 | `block:4f824eefd7bb320293e3f66ba2e8a603b4797c12b93440eae4768ed7fa22f2a1` | `block:1b729e1d57f520839579f109c2cfd0bd7f690b74c1d2a9e868032d40f0a63ffa` |
| S27: classified; Part IV, Item 16 | Item 16. Form 10-K Summary | 1007–1010 | `block:aa593afb27aa917b29ee025626b2faea6f08e6f98154469238c474206b56ac77` | `block:25a9be764c095779faaf52c49d36409c5450ac46533b96a294ac58ec8e1d3772` |
| S28: unclassified; Part unknown, Item none | SIGNATURES | 1011–1016 | `block:5932b91f55cd9b65cead5ff5a4249bc15d6ccecd442b068848bacfc14b6fce16` | `block:8431f3aa3b1878459ffc3f921caa7ae4cc2c762396e930b88ff1386900cbece1` |

### F13 — Amazon — 0001018724-26-000014 — 10-Q

- Filing date **2026-04-30**; report date **2026-03-31**; split **development**; **619 blocks**, **15 detected ranges** (11 classified, 0 ambiguous, 4 unclassified).
- Document ID: `document:12e4f6041351020db0ab615654221fa03f4c919df5d4a48b732c40d34ad6f56c`.
- Source: [amzn-20260331.htm](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000014/amzn-20260331.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/e6/e6b80e48612abe3a0a8256e5ff3b5637cd4be94c12dc18cd3d7106667294fb8b); 1,241,350 bytes; SHA-256 `e6b80e48612abe3a0a8256e5ff3b5637cd4be94c12dc18cd3d7106667294fb8b`.
- Logical output SHA-256: `b9a935a272c3bbe24984aef5e3118c6784693c3673eb620ed867f1894e35aab8`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **619/619** locators; fetch `83ea59bd-9c6f-4340-b4af-e44c8e2b9c83`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): none.
- Unclassified/ambiguous ranges: S0 0–41 (unclassified; Part unknown, Item none); S1 42–42 (unclassified; Part I, Item none); S6 421–421 (unclassified; Part II, Item none); S14 614–618 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×2, `non_item_section` ×1; total **6**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | Table of Contents | 0–41 | `block:5c4c5f4a6fb1209b58225bc4100b99345f2d745366e12695e0159b5067962fc3` | `block:f5e0ef540d661086b30301bf7f233ba65add1419807a97287b5e1151ed37dac9` |
| S1: unclassified; Part I, Item none | PART I. FINANCIAL INFORMATION | 42–42 | `block:f9c26cb62a9b8abef20b1d58c368e6073d2da30cf40fbbccef2d3006839d109c` | `block:f9c26cb62a9b8abef20b1d58c368e6073d2da30cf40fbbccef2d3006839d109c` |
| S2: classified; Part I, Item 1 | Item 1. Financial Statements | 43–287 | `block:59a5703015b36a268634a6c6fbe9e2f26cbd5c0a70dae2b338b2eb9706a38c09` | `block:f3398d4a5468bd2bd5d325c08bf7a5be2b5d2fc3f56b014f70d6bd8254f1a4e9` |
| S3: classified; Part I, Item 2 | Item 2. Management’s Discussion and Analysis of Financial Condition and Results of Operations | 288–400 | `block:1afae223af6146e3297bbbf51f79581e335d5bcf0a5cb1586ac22c4d779903d1` | `block:de7cbf438e6d20808ffd22cfd635c33cc3622069f9601dffea850260d2fdccd1` |
| S4: classified; Part I, Item 3 | Item 3. Quantitative and Qualitative Disclosures About Market Risk | 401–414 | `block:1fe03ba102522a940eaf7d3cea75e53c59c6b4271f96de8ddb611e55d15467e2` | `block:97557f9c758be2547cfbf19373e50fe2a6496cea144271e8b6cf73f37330ed62` |
| S5: classified; Part I, Item 4 | Item 4. Controls and Procedures | 415–420 | `block:2467921405118ff1899d5d947a86a2cfbfa379c4cfad96e0a79672738defeebe` | `block:6e052812485fd5982015a64ebf7fe95792a1b3efc50bf18abf396fb328fe600b` |
| S6: unclassified; Part II, Item none | PART II. OTHER INFORMATION | 421–421 | `block:1bdbc6f2a005698d72f244d44e51009f3d19754a7c1f5795a09a9c7935c2022f` | `block:1bdbc6f2a005698d72f244d44e51009f3d19754a7c1f5795a09a9c7935c2022f` |
| S7: classified; Part II, Item 1 | Item 1. Legal Proceedings | 422–423 | `block:fa6fdeb410bdc6284e8a926e424f52c9dc88e3e63fa9f00c599b03029a3a7847` | `block:789bc1b5ad05d01c306b91c2b0d526e9264e629b34017eeeef668fa81b438018` |
| S8: classified; Part II, Item 1A | Item 1A. Risk Factors | 424–596 | `block:e5e936e3891c2e43b8a065e61bb2cae760a60f2e083470e9890a28c70865cdc1` | `block:e1010df51890ee3350b687fc55faca5443891da9cddf70f99c0b1427f0ab1e62` |
| S9: classified; Part II, Item 2 | Item 2. Unregistered Sales of Equity Securities and Use of Proceeds | 597–598 | `block:8d5494029056450ff8be431107b9bd5c4ac494cdc549a88fc0be69daf5ea9cff` | `block:b7c69e9945f6181540036cf07980a4fd3451db16e0e0bb1e314a08fb6490a358` |
| S10: classified; Part II, Item 3 | Item 3. Defaults Upon Senior Securities | 599–600 | `block:5090863749d6919ce57bf5b5b895ddb69fb1682dfa92965092f9af8d2b9fbc6c` | `block:dd0074b375dbd8560ae792f7be088e007e6d477cf42c534566019b125964b3d2` |
| S11: classified; Part II, Item 4 | Item 4. Mine Safety Disclosures | 601–602 | `block:158eb1a13fbef715fec71d002cbcb88399a85899ec78ff849f89fad3ba00b3c9` | `block:4fb023e1dd51152cc4ecaed28c7ba160e03ae400b4a84350b2f4ed7438785312` |
| S12: classified; Part II, Item 5 | Item 5. Other Information | 603–607 | `block:aefe7e03920a4b7b2e4472c285b48fc36729e90800f3b084df87b508242b3ea5` | `block:cccb367ce7d2db7ed9badb9bcba5c95e185f3193dd65cd43600b36d4111618e2` |
| S13: classified; Part II, Item 6 | Item 6. Exhibits | 608–613 | `block:070776d4ec4e07a3b37a9441f19bb48c373e7e7f960b708555e885c9a1a6299f` | `block:44ca336ea2dc79df040c9045e2bb29deb28f7a3c8624c203cc57effb672e75a7` |
| S14: unclassified; Part unknown, Item none | SIGNATURES | 614–618 | `block:9ebc23ff47bc87079fdaeb7f822cbce985a47cef2c74bf1fa5f2fa44d930d8da` | `block:2f9693c46b1c45ce044b2069226c8423e858d0ed50e63f68485843ca4eb4b721` |

### F14 — Amazon — 0001018724-26-000026 — 10-Q

- Filing date **2026-07-31**; report date **2026-06-30**; split **held_out**; **639 blocks**, **15 detected ranges** (11 classified, 0 ambiguous, 4 unclassified).
- Document ID: `document:244d488043fca1871cf92393a93cecaa25b9d8542f45b9b4384dcfc7b5e8b7ab`.
- Source: [amzn-20260630.htm](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000026/amzn-20260630.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/71/71f119d4c8e9f2347b929b794f9139d263d55c765f845a6856162da4126c3416); 1,591,528 bytes; SHA-256 `71f119d4c8e9f2347b929b794f9139d263d55c765f845a6856162da4126c3416`.
- Logical output SHA-256: `af60fab708768d51dc5eb34283428784771bece3f8e122a99bf845c897ae7551`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **639/639** locators; fetch `4ae881c1-63a8-4fb5-b1ae-9521e61d2b73`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): none.
- Unclassified/ambiguous ranges: S0 0–41 (unclassified; Part unknown, Item none); S1 42–42 (unclassified; Part I, Item none); S6 441–441 (unclassified; Part II, Item none); S14 634–638 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×2, `non_item_section` ×1; total **6**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | Table of Contents | 0–41 | `block:a1cb081320616f6001f51153e2d5732cc82a8d1442cb3c293efad392b4da2723` | `block:b50748880deb810f74ea749cdc5b00811631dc1b0bd6eeaa270b18d2a7b0ce72` |
| S1: unclassified; Part I, Item none | PART I. FINANCIAL INFORMATION | 42–42 | `block:4785a0352f621db6803f02281ed450ba87711ac5b7a5da5a7f3ebafff6e4c80a` | `block:4785a0352f621db6803f02281ed450ba87711ac5b7a5da5a7f3ebafff6e4c80a` |
| S2: classified; Part I, Item 1 | Item 1. Financial Statements | 43–303 | `block:21bee99da701608e2faccb60cbe60ab8377eba4fa8c1eda2e4698b318af50340` | `block:9a36cb0b51b3df8a2058d1050284b6736a7ce3f5cc6ec3ce0626037558794e38` |
| S3: classified; Part I, Item 2 | Item 2. Management’s Discussion and Analysis of Financial Condition and Results of Operations | 304–420 | `block:2e1beb8ee142955b4a98d47ca9ddfd7e979d7ee44b904be38b88046b294c61be` | `block:3470eb30bcf86b0d49f1efcba85b97905d129567dd08d0cc66d8994cb4ff998d` |
| S4: classified; Part I, Item 3 | Item 3. Quantitative and Qualitative Disclosures About Market Risk | 421–434 | `block:9e79ee2299c7a2a9d3765cbcbae78c43d7ebb69aadd7d34af9c0f1ade26870c9` | `block:5dcd7a6617c452cf9eace74d91762b7cbc60d97670038608db210a22a419df5b` |
| S5: classified; Part I, Item 4 | Item 4. Controls and Procedures | 435–440 | `block:5d64af70af94505ad760519aee17440a0ebbacd9b4cc3c5a74fb7d91d9dea2dc` | `block:ebd55c37f67382f47f6ce714b74b8304653e8e2e6b30444175cdf4cc2f5591fc` |
| S6: unclassified; Part II, Item none | PART II. OTHER INFORMATION | 441–441 | `block:c9dc10965801151717e22756b1222f30e239789ca9c9ab01d0cdf3beb8c24c9a` | `block:c9dc10965801151717e22756b1222f30e239789ca9c9ab01d0cdf3beb8c24c9a` |
| S7: classified; Part II, Item 1 | Item 1. Legal Proceedings | 442–443 | `block:72d930f5f611826d9db659d72b10adb02db8f67639637f71cfe69d2ec2f734d1` | `block:1f9c4086a1c7575c9f2957c2d01a823df26ff70bb8859455fb5608e7ddd49790` |
| S8: classified; Part II, Item 1A | Item 1A. Risk Factors | 444–616 | `block:f95c29623e19245d916dcc499c937786c82e1961b1ec98cd3c6069c0f3849a9b` | `block:bfc5d8bbdd47d8d06ea4ecd18079b069b7b1bf2bea28a9930a439655c37e8681` |
| S9: classified; Part II, Item 2 | Item 2. Unregistered Sales of Equity Securities and Use of Proceeds | 617–618 | `block:89646ba61332644c8e30aaf99aa86f148f501e88a893ad293b8facf572a0d304` | `block:023ec34b6f857639dadda1c5c45c19b11f9db87f9eb7538cba85f8e52f1c70dc` |
| S10: classified; Part II, Item 3 | Item 3. Defaults Upon Senior Securities | 619–620 | `block:81ffea5070426686f6c76c455754f6f2f44e8cdb75529a22fde7a03cbf724ebc` | `block:9f0f49d2045e33dc58e2473b540573cd10f79ed9c3675d62aa9ba644f345788f` |
| S11: classified; Part II, Item 4 | Item 4. Mine Safety Disclosures | 621–622 | `block:ba203a8bb5e043947d7879edd67f334b4f9e6009724133882ff00a6f5e38f18c` | `block:170d7a02be73f2f285d56f6b4ef3d31ed7ab851fee58b7ad2632d184204dfd91` |
| S12: classified; Part II, Item 5 | Item 5. Other Information | 623–629 | `block:079832c86562682a58444e941fb1d4f26faab99f0c8ffb504fa80c484906f9d3` | `block:0c0da8a4cec76836f5c96421b6ed780b423418737433962d94b92b4ef4281e60` |
| S13: classified; Part II, Item 6 | Item 6. Exhibits | 630–633 | `block:db971d727c80c8a9f39cde615631e0dbbc7161e222a3408628fe432a05e6c346` | `block:ca8dd5740a75034e06ca1d07b4734e0bfa09e5609d2a835748cc50eae16acaf7` |
| S14: unclassified; Part unknown, Item none | SIGNATURES | 634–638 | `block:2e58feebef8ee55eb901be5531d0ca8617913513eb2a840f50890f69339230e6` | `block:08d9b7d6095261579b7b46a188e6eba8cfb376b3409ab21c6e1b5db9f5994374` |

### F15 — Alphabet — 0001652044-25-000014 — 10-K

- Filing date **2025-02-05**; report date **2024-12-31**; split **development**; **1,380 blocks**, **29 detected ranges** (23 classified, 0 ambiguous, 6 unclassified).
- Document ID: `document:e049d1df6916c050fea8957e4e2d269743113f4186a6048db0152fba73f615a3`.
- Source: [goog-20241231.htm](https://www.sec.gov/Archives/edgar/data/1652044/000165204425000014/goog-20241231.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/7b/7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d); 2,528,450 bytes; SHA-256 `7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d`.
- Logical output SHA-256: `e487a9e081ba8de1abf61550372eda8d7fb27c9ba8b0ec2c0108007b430daf55`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **1,380/1,380** locators; fetch `2e0f892f-49ea-47ee-9e4c-2c403ed965ac`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): none.
- Unclassified/ambiguous ranges: S0 0–86 (unclassified; Part unknown, Item none); S1 87–87 (unclassified; Part I, Item none); S9 406–406 (unclassified; Part II, Item none); S19 1327–1327 (unclassified; Part III, Item none); S25 1341–1341 (unclassified; Part IV, Item none); S28 1369–1379 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×4, `non_item_section` ×1; total **8**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | [TABLE] | 0–86 | `block:cde902bb881aa8fc557fbfd420aaa2a33c6214cb0a699989ac704c03f3b3be8f` | `block:487a329043fe815dfd45656692f5d6ed98af50aacabc704a5e4e35d48d5a0310` |
| S1: unclassified; Part I, Item none | PART I | 87–87 | `block:4956a54d194ebea102996ee3cb1c907411198b4e80116829cdceab1f29e7800a` | `block:4956a54d194ebea102996ee3cb1c907411198b4e80116829cdceab1f29e7800a` |
| S2: classified; Part I, Item 1 | ITEM 1.BUSINESS | 88–200 | `block:b699c9d9e32c7a4dc441e7cb9eb0a899f2d0eba073e767a4fa54b3bea6365126` | `block:da73d863aca6a3cc954f5f17e175ae5830ee6009b1c1c6fce55dcb52a57b9817` |
| S3: classified; Part I, Item 1A | ITEM 1A.RISK FACTORS | 201–387 | `block:90571f6b108e29d5d9840a23760f379dbb9b332ec1bd4c6a5c3fd7475139b238` | `block:0a5623ed4645f12471759b9e32f4cba970eaea5e9cdc996763ce410a5580d241` |
| S4: classified; Part I, Item 1B | ITEM 1B.UNRESOLVED STAFF COMMENTS | 388–389 | `block:674404a4bbff7e8740e221b166305ebc0ac830d88f92964a9f668a12d21d4193` | `block:93f9938399cb654b35c13a21d116577776ec50f4f685b40d45adefa0bfcddee8` |
| S5: classified; Part I, Item 1C | ITEM 1C. CYBERSECURITY | 390–397 | `block:d37683e743f6bf921b4f53cbb729c7e1ee9041917aee1bab48108838c72ae17b` | `block:414d7fb94a127acdd41f8f2f699e8c93ae153aa73c0a68afdbb48438fe270d84` |
| S6: classified; Part I, Item 2 | ITEM 2.PROPERTIES | 398–399 | `block:c0430846232bcbfc19e633579a5c2ebb5fbbcd8a2c0d671994a19341f53de570` | `block:28a5f16d9372421780cb68b004ef8679ce73da0aa2177362a9d39092cf9256f5` |
| S7: classified; Part I, Item 3 | ITEM 3.LEGAL PROCEEDINGS | 400–401 | `block:f1b05b40c6532e1fb038572cf3421fb4f15bf19765a8b4fb5a3060add28a0204` | `block:8359d437e667c628c81e696ba89a4c956193fa417ca8f9121c15fb66140b3774` |
| S8: classified; Part I, Item 4 | ITEM 4.MINE SAFETY DISCLOSURES | 402–405 | `block:ea24d007ab2450793d63ead04d8f810c7336d0817d3d20e891a4e1ddf1b98a23` | `block:7c0cea4fbc4e563b00abed3283e2c0c40d7db7bfdcccd469a1d301a5ceefd506` |
| S9: unclassified; Part II, Item none | PART II | 406–406 | `block:f4bfa7268af8b7fb10aa98502dd97a0070fcef78f14605fd0ef11e89cdfe6efb` | `block:f4bfa7268af8b7fb10aa98502dd97a0070fcef78f14605fd0ef11e89cdfe6efb` |
| S10: classified; Part II, Item 5 | ITEM 5.MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS, AND ISSUER PURCHASES OF E […] | 407–436 | `block:72a2bfb707f3ed3d9536b8f30e8ce5a40f6553dc77bd5f614c8541d83fff5882` | `block:5a32f8e3bf41e90d5b5d2d739317e0c80d5cd9c924f1be5a78dabaa03a7e6c92` |
| S11: classified; Part II, Item 6 | ITEM 6.[Reserved] | 437–439 | `block:19969031adcf4f4c62b44dcc52c0515267f176c7c7e38247664a305ba352643b` | `block:36bd24f9cd0c3ad531bb7815c8431aafc8b76f57c295745adc6308998ca3add4` |
| S12: classified; Part II, Item 7 | ITEM 7.MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS | 440–740 | `block:8a0967ac564ea5ecad8ee6f1c2ccd8e6bf56d60c306be95ff6f5d14bd2c207d3` | `block:b9d051d87349c1386d16b19a33960c056b3e165c2d776512a9f0b4d36960dfe3` |
| S13: classified; Part II, Item 7A | ITEM 7A.QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK | 741–770 | `block:2414cded824eea0b6beeee011df28a4e4d2be58b90447d1602fbe98801d29050` | `block:2a210f2f04e4beea90e91accbb50f1bd83a4dae23637edd8ee95e97cee1f589d` |
| S14: classified; Part II, Item 8 | ITEM 8.FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA | 771–1297 | `block:84e304937096218fc0f2424edb09eb71e8d21d8ce53fa144c3fa95949e4f94a4` | `block:2c5426eac3a06fb1367a9db63d8cbe9ac6e9d37f6b89f367200f7c22b663bb03` |
| S15: classified; Part II, Item 9 | ITEM 9.CHANGES IN AND DISAGREEMENTS WITH ACCOUNTANTS ON ACCOUNTING AND FINANCIAL DISCLOSURE | 1298–1299 | `block:abe3ee7b72af612398117cd61ec9f91e4626b560190e8e7b281c0f014ad97ac7` | `block:d8a3830e76545a7cbff21616af6c2c642a83222c98ef69c73f5137980dee1927` |
| S16: classified; Part II, Item 9A | ITEM 9A.CONTROLS AND PROCEDURES | 1300–1309 | `block:1716976825d0a5e6a3e286b2b3c24ee37ce8d525332dd8d1d94dd153ce4de695` | `block:5bb6e82e376645c29fa14257c43e381ec467f94d3137b1096e603ef928d03578` |
| S17: classified; Part II, Item 9B | ITEM 9B.OTHER INFORMATION | 1310–1322 | `block:70fb33b0f19f62c0f2c24fba5e22372ac481e1cb0e266d2b6455a382ed45a934` | `block:6bdcd5ee7ae2ca35a3b78a197b656205a815962965ae1a75e8d7490b98dcf93e` |
| S18: classified; Part II, Item 9C | ITEM 9C. DISCLOSURE REGARDING FOREIGN JURISDICTIONS THAT PREVENT INSPECTIONS | 1323–1326 | `block:44e60ae5d8d67dc0bebab316f4865dc13e80346537d183bd82e6f225376b7979` | `block:ac822c8176d9b55654cce92bdd1d6f0d4003a2c6f959af25f57926d671aac149` |
| S19: unclassified; Part III, Item none | PART III | 1327–1327 | `block:32f6fd09d24d481113260e98cf7498482195c035ae7a1006262d3d4d19baa4b1` | `block:32f6fd09d24d481113260e98cf7498482195c035ae7a1006262d3d4d19baa4b1` |
| S20: classified; Part III, Item 10 | ITEM 10.DIRECTORS, EXECUTIVE OFFICERS, AND CORPORATE GOVERNANCE | 1328–1330 | `block:607293154a178818b8661bc7a3ee7ab72e03de17114d5a7bf4153fdeb0c02a36` | `block:9bfd716e24d099640f3b8dad509cf099a881f189ed236deab8c163bd92583216` |
| S21: classified; Part III, Item 11 | ITEM 11.EXECUTIVE COMPENSATION | 1331–1332 | `block:8beaf84c14a8a22ca6ba3b28b3a575d7a1665cba71fc0b22cf39a183e4d43692` | `block:b88d241d9c5f5f6cf4ee20bd557f566f46875509306737d56e2a7067ca345f43` |
| S22: classified; Part III, Item 12 | ITEM 12.SECURITY OWNERSHIP OF CERTAIN BENEFICIAL OWNERS AND MANAGEMENT AND RELATED STOCKHOLDER MATTE […] | 1333–1334 | `block:21a509b2d5cf7b5ee0bfe9776f8803e7f69c8e38f9a465773e4b79c6f71e10a9` | `block:eb2b30712f2696e90dfcd94a36e7fa4d6abf994ee1e29a6c9d412002cd1a6ba3` |
| S23: classified; Part III, Item 13 | ITEM 13.CERTAIN RELATIONSHIPS AND RELATED TRANSACTIONS, AND DIRECTOR INDEPENDENCE | 1335–1336 | `block:62fe3472780aad908e1b45600f016ab686610fdb2becbed86b63c9cd87c12ecc` | `block:d187b03f030860ca597d66859e323dd510a5ebaa21e6e47978ba9ff7e212966c` |
| S24: classified; Part III, Item 14 | ITEM 14.PRINCIPAL ACCOUNTANT FEES AND SERVICES | 1337–1340 | `block:0042e631d5ce0181da7b050a5be0f375617ac5da8709ce498e826e79c4a63730` | `block:cb8ad3d6ddc000192dec29801e41b2a8fbffd1a558df75ec81df809bd5ea3bee` |
| S25: unclassified; Part IV, Item none | PART IV | 1341–1341 | `block:62855665b87c808e35b6ddda7cd46af72d432876315a0b8dea2c0edf8a81a53e` | `block:62855665b87c808e35b6ddda7cd46af72d432876315a0b8dea2c0edf8a81a53e` |
| S26: classified; Part IV, Item 15 | ITEM 15.EXHIBITS, FINANCIAL STATEMENT SCHEDULES | 1342–1364 | `block:06bc7885a1fa308cf658901e3fb98a066026c8ed886897b3b271bd233cef3e8f` | `block:6acbdc6b29c4eb640e842577697892d67ee9b35620bc5eb6aa634b85c6d6fc31` |
| S27: classified; Part IV, Item 16 | ITEM 16.FORM 10-K SUMMARY | 1365–1368 | `block:19d8e344699676569a0df2b40c1cbcc1c1da74ea664b70c10d39f583161e128e` | `block:e963a81aa6c6376ee408a23e08e97db5516e291290488ad169d5c475d2f490c1` |
| S28: unclassified; Part unknown, Item none | SIGNATURES | 1369–1379 | `block:d1b4945db63d249a155e1ef0ce3bbed4c781a38033cef7e2dd23993eda70626e` | `block:81919e86915f95e4111eb415a219e58c29db5e7594995c92d3333dd95994d225` |

### F16 — Alphabet — 0001652044-26-000018 — 10-K

- Filing date **2026-02-05**; report date **2025-12-31**; split **held_out**; **1,334 blocks**, **29 detected ranges** (23 classified, 0 ambiguous, 6 unclassified).
- Document ID: `document:25d07feb32ed9f44011b77d43d3af179a67c5db524164ac85e2b86f212f8a86b`.
- Source: [goog-20251231.htm](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/55/55433ab65713c9cfebd65dc33c8e2d116e8a1d60c64a955d20cd2171ee8ceecc); 2,616,605 bytes; SHA-256 `55433ab65713c9cfebd65dc33c8e2d116e8a1d60c64a955d20cd2171ee8ceecc`.
- Logical output SHA-256: `04be4c0d11e2173b975d215b12cebd9feeb7ada9c5435141486479def406c95e`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **1,334/1,334** locators; fetch `764ce16a-6ab7-4030-b6c3-01fc6530cbde`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): none.
- Unclassified/ambiguous ranges: S0 0–58 (unclassified; Part unknown, Item none); S1 59–59 (unclassified; Part I, Item none); S9 356–356 (unclassified; Part II, Item none); S19 1279–1279 (unclassified; Part III, Item none); S25 1293–1293 (unclassified; Part IV, Item none); S28 1323–1333 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×4, `non_item_section` ×1; total **8**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | [TABLE] | 0–58 | `block:ea717688f404b7758c06948ea6980126fa70b352f9d0c537ab06b76976e65b4c` | `block:cd89ac1513f4aa2d2d61abb06e439696995ca6f9c19e145066bf98029d19ed87` |
| S1: unclassified; Part I, Item none | PART I | 59–59 | `block:d64a26f7d252b1545d4f26b83ff78f721603752d7d2a667a131be719a34266ef` | `block:d64a26f7d252b1545d4f26b83ff78f721603752d7d2a667a131be719a34266ef` |
| S2: classified; Part I, Item 1 | ITEM 1.BUSINESS | 60–150 | `block:71ff7e9a6d8e8414995c2226e3359ca6df00a850bb36db92c7bbf06917c6ad82` | `block:af7db636c7b27bc5c71ff2b0c2eccde9abd4ad8cfba434e5873ea36617edeb60` |
| S3: classified; Part I, Item 1A | ITEM 1A.RISK FACTORS | 151–338 | `block:7288807d1cf08bba95d2df027072120c75deb8ad6b5bbe9872f149fcb5d3aedf` | `block:806f67a4d512a87cdeea4720d078d36910b12a96756678a5e4d79275fd2b2daa` |
| S4: classified; Part I, Item 1B | ITEM 1B.UNRESOLVED STAFF COMMENTS | 339–340 | `block:fb0cd6a7901eb879ae28cf22d2ccd1fc81fb23e309bd938c1223433416586cf6` | `block:cab042c5bf365ced9a985a20583968cee4a4f2685ed82a8918c1febcd7057d5d` |
| S5: classified; Part I, Item 1C | ITEM 1C. CYBERSECURITY | 341–347 | `block:ed52cf93930d29fd46ad69c65c3c6470ba458d106c8af0debed6dea3746f057e` | `block:23a717ef70c8bf1c8ce66ec4f05ddfa7a21334418aa4a9db026e14e78b41dfde` |
| S6: classified; Part I, Item 2 | ITEM 2.PROPERTIES | 348–349 | `block:1a262e71b5386c5240356f107f91eed54232bf66bbe7ba5385960d8c98e116e2` | `block:5395ad3d3fa26ec08e83354929ab7c635183a84761dff164c83ee86374eed3df` |
| S7: classified; Part I, Item 3 | ITEM 3.LEGAL PROCEEDINGS | 350–351 | `block:c7d357f06aed675b604af43177851e83030b56cfec008dfb65426ee53560952e` | `block:cd2dbb81d4d95cd24f77d25b818528a38b252e3c0a9091a5ca14e75621c0c06c` |
| S8: classified; Part I, Item 4 | ITEM 4.MINE SAFETY DISCLOSURES | 352–355 | `block:aea88f33d71b9410a2a44994cf6905be2dc75453a9ccf58d7629ac7f2317e9bc` | `block:c744b63114b193aafebc7da440bc7506e7d7f6b8bf6b2097100b49d61ab74c73` |
| S9: unclassified; Part II, Item none | PART II | 356–356 | `block:9e62edb41dbbc17abcb1612aaa7799e32b2053c675bc7138701bdad78cd81441` | `block:9e62edb41dbbc17abcb1612aaa7799e32b2053c675bc7138701bdad78cd81441` |
| S10: classified; Part II, Item 5 | ITEM 5.MARKET FOR REGISTRANT’S COMMON EQUITY, RELATED STOCKHOLDER MATTERS, AND ISSUER PURCHASES OF E […] | 357–386 | `block:0e2fb780031fd8860c7c5d8d4e59b50b79ef5f4a6480e95007cf91015f1688cb` | `block:8e0f271fc5091776210f3af51ecf920f09a8dd535ce7e6b468daf09985305e2f` |
| S11: classified; Part II, Item 6 | ITEM 6.[Reserved] | 387–389 | `block:f3b5a7963d509a237da7fc8e735cc369f1c75daf7a946bcd19887edfd5fb0798` | `block:b0ca78bf8609bbdfe0016f4539c58818db089ed4712985f81d84e4261916735d` |
| S12: classified; Part II, Item 7 | ITEM 7.MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS | 390–671 | `block:1e6694c68b34df4b877cce574f16d0c724e7bfdac219109d75a0e048d42fa782` | `block:17034305413b1be345b1c95783db3b01a2aa5906d43d9c869f05e4d31d35a799` |
| S13: classified; Part II, Item 7A | ITEM 7A.QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK | 672–701 | `block:281b42419b6456afcc8215c7f60e67c99a1372dceb419850571d22176f5ce397` | `block:3459e53df15388d2ffa0db8aeec24ebea6ba4abb0c9a512d7b44c0e497806eee` |
| S14: classified; Part II, Item 8 | ITEM 8.FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA | 702–1251 | `block:149b95b079be6064000ea8a2af2c6b67fb86b590eff2afe25dafae71b5e8ed59` | `block:354f58fd6cb361d54feaf2c62ced65be575873dfa7effa6a3cd3ff0e53aa434b` |
| S15: classified; Part II, Item 9 | ITEM 9.CHANGES IN AND DISAGREEMENTS WITH ACCOUNTANTS ON ACCOUNTING AND FINANCIAL DISCLOSURE | 1252–1253 | `block:70d77af72a2cd13b8865b6eb4a30440d7e1092648d57701c1987e794a2904696` | `block:fea5f7e0680ff57519631781603bb2aa5354b0ab2fe6e336e35304a1f20a0cf2` |
| S16: classified; Part II, Item 9A | ITEM 9A.CONTROLS AND PROCEDURES | 1254–1263 | `block:4d02e8dadde6032017363a380f2a8f68268b406d914502d55b57a65f59fc2206` | `block:aceb647b971db9c2ac64068528a7adefefb3c91c780ec797177197e7fb3a4b37` |
| S17: classified; Part II, Item 9B | ITEM 9B.OTHER INFORMATION | 1264–1274 | `block:41d43281adece64bb12561dbe818a756afec9b4e05ae4137df2b922013f4e7f6` | `block:db196919c27dfc29190abafad128eff802067aff98f51f384312078d18dba58d` |
| S18: classified; Part II, Item 9C | ITEM 9C. DISCLOSURE REGARDING FOREIGN JURISDICTIONS THAT PREVENT INSPECTIONS | 1275–1278 | `block:a9723c2aa1fb95c8c20a5db80a346a5f526bef8a04ab5515b2ea9977db74305e` | `block:778d795177e1f365b76b5706dba6b1605c96e0c2143fe2fab5b0e2a5a899735c` |
| S19: unclassified; Part III, Item none | PART III | 1279–1279 | `block:92c51aa3247b89c68cbeccadb23e4689751d7a0a53eeb6bf96dc88b151581030` | `block:92c51aa3247b89c68cbeccadb23e4689751d7a0a53eeb6bf96dc88b151581030` |
| S20: classified; Part III, Item 10 | ITEM 10.DIRECTORS, EXECUTIVE OFFICERS, AND CORPORATE GOVERNANCE | 1280–1282 | `block:03d99c9b26e345c2a426b05e5dcbdff4801bea11c99676454e9bc79f60d71b32` | `block:7a60ff90c8bcf21e8ee3e5a9fe1788c77559421138400b99b0e2de0eca92e1f6` |
| S21: classified; Part III, Item 11 | ITEM 11.EXECUTIVE COMPENSATION | 1283–1284 | `block:2777eb77b93602040836279fa339cb86ed8afbca6eb565b71c95974d3b658fc8` | `block:80cc13d6e97e67450b6008c5aa5bd11d5a6e89337ef7a0692a6934b34968b672` |
| S22: classified; Part III, Item 12 | ITEM 12.SECURITY OWNERSHIP OF CERTAIN BENEFICIAL OWNERS AND MANAGEMENT AND RELATED STOCKHOLDER MATTE […] | 1285–1286 | `block:494c6c28ff6de76a9410bfb878bc34bfb808677e53fb772468a7dbd303e3f1d1` | `block:8e4bc852fa85fdcb37ba177b732ee965ec524a581b96b6d492cf50e195411928` |
| S23: classified; Part III, Item 13 | ITEM 13.CERTAIN RELATIONSHIPS AND RELATED TRANSACTIONS, AND DIRECTOR INDEPENDENCE | 1287–1288 | `block:7e32e61f61f339546e43a306c9f565769e3ef1e1d6deff28f416f95dde567bd1` | `block:69795b87c3e2357ce03e8fdd582ec579634a823f963a72e8500219a7f9149df9` |
| S24: classified; Part III, Item 14 | ITEM 14.PRINCIPAL ACCOUNTANT FEES AND SERVICES | 1289–1292 | `block:fb871e84eebcf4ea12adc33645f8d70cf3bc2a0e5e52eb298649faf940f5f615` | `block:439315a52f095c9d5737124bb0c978c667dbe59572f50953cde3a5a2412ce957` |
| S25: unclassified; Part IV, Item none | PART IV | 1293–1293 | `block:2ee0ac4477a5900bfd384cf588809e3b86a557645f379dc7dd75f238e0d7eef4` | `block:2ee0ac4477a5900bfd384cf588809e3b86a557645f379dc7dd75f238e0d7eef4` |
| S26: classified; Part IV, Item 15 | ITEM 15.EXHIBITS, FINANCIAL STATEMENT SCHEDULES | 1294–1318 | `block:cfd2f1cee0eb15d8aed00717337250879d3789421a8c5096c44ad47650116561` | `block:64954292682d5b62378d6c2deeca8861883b060d067a97333b96301c3d553508` |
| S27: classified; Part IV, Item 16 | ITEM 16.FORM 10-K SUMMARY | 1319–1322 | `block:87cad58bc0258cb8ca0bc820f270c9a22c0a2d678aab1e1a7d182e3df31717c8` | `block:7fe3ec304e697de703c7911e657b5f9ae8bab7f79bc3cf12397d386765241f81` |
| S28: unclassified; Part unknown, Item none | SIGNATURES | 1323–1333 | `block:0aac4139710802d6bef1e850cf153525f09bc62a04809796f6598e919c4f82bf` | `block:417b876b953e9f2390eb15372ffcdd9a2d1bc781941b37e74252151346273c42` |

### F17 — Alphabet — 0001652044-26-000048 — 10-Q

- Filing date **2026-04-30**; report date **2026-03-31**; split **development**; **692 blocks**, **13 detected ranges** (9 classified, 0 ambiguous, 4 unclassified).
- Document ID: `document:7e4c54f8a342fe573df488ab14a804a0cb3ae65923a0ff4eca7ee0cb3a546719`.
- Source: [goog-20260331.htm](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000048/goog-20260331.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/0d/0da733204ca3463c96d324c3620ab2794bce9566ee7a6586100b66634a98aca0); 1,714,819 bytes; SHA-256 `0da733204ca3463c96d324c3620ab2794bce9566ee7a6586100b66634a98aca0`.
- Logical output SHA-256: `bcf4f84efdbbce500929a3115a9f9b6d95929fe9db98fe6fcaaa55a5c2cfacaf`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **692/692** locators; fetch `b828f773-19bd-4686-9157-1ad855f4724d`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): II:3, II:4.
- Unclassified/ambiguous ranges: S0 0–48 (unclassified; Part unknown, Item none); S1 49–49 (unclassified; Part I, Item none); S6 653–653 (unclassified; Part II, Item none); S12 687–691 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×2, `non_item_section` ×1; total **6**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | [TABLE] | 0–48 | `block:b1859a4e60ce1ad4b9ad564b7c96c173debbd4d28cc502dcea7d2a02d19be56f` | `block:d959cb85daa3b46ae602680e195759f82aaa7716c12e9a18241c16649edd9ba0` |
| S1: unclassified; Part I, Item none | PART I. FINANCIAL INFORMATION | 49–49 | `block:0d5aa26dfc831cb443a5cc3c22941b47e1d7d4cb02b16312b02f8e5d52c83a31` | `block:0d5aa26dfc831cb443a5cc3c22941b47e1d7d4cb02b16312b02f8e5d52c83a31` |
| S2: classified; Part I, Item 1 | ITEM 1.FINANCIAL STATEMENTS | 50–392 | `block:b77b92d1495437214b72e7cd0b291b2ff9f772bbc1cccc9475e23d24a243eb8a` | `block:f90f30cd1e08270ea6fab30b3de1ea183dfb82adc5d76af5337a7c388ec09040` |
| S3: classified; Part I, Item 2 | ITEM 2.MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS | 393–641 | `block:8cb99703a045c255b09550f92e72358254c50ee233a1c2cf69df0155fc809fb4` | `block:c75802235b5fca6ece249a950ce6c1ef20ae9d44c873893139be5b171fef7045` |
| S4: classified; Part I, Item 3 | ITEM 3.QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK | 642–643 | `block:e77f9340b903be3af14a2d88e1f00756ff82ca8cfeb2665fa5995295de09045d` | `block:f3d5f3ee82c072e717bc2bc6a3654405535f89caf222db66bb03322175145d19` |
| S5: classified; Part I, Item 4 | ITEM 4.CONTROLS AND PROCEDURES | 644–652 | `block:c37ad54abc1b81a19985e7411de7b108ac94dd79fae7fc3c7931ccfbd80dfe69` | `block:afbcc2307c8dd07eb75798475152f0267373f032d1e825c271b4d5b21c0b2aa1` |
| S6: unclassified; Part II, Item none | PART II. OTHER INFORMATION | 653–653 | `block:8f2a8a8b312fb633a28b63bf25ba4cecf96a097b979188ee30af8263c6684323` | `block:8f2a8a8b312fb633a28b63bf25ba4cecf96a097b979188ee30af8263c6684323` |
| S7: classified; Part II, Item 1 | ITEM 1.LEGAL PROCEEDINGS | 654–655 | `block:0f07e44db3f2b1535a653d6d2c1685d40897fa98a753549977b4dab7942d6e0f` | `block:6dafb9aa006217a5bfe9a463c9dee35d8df026472a447125c57d567dd1d0a536` |
| S8: classified; Part II, Item 1A | ITEM 1A.RISK FACTORS | 656–669 | `block:83555ee2d54f531cfdf885a5f4a883e5b9bb56d121ec9e0582859adfeaa6eb98` | `block:18b7c410a50e8c73924ffb4c913ee1602714baeec8504422872f99943d965cd1` |
| S9: classified; Part II, Item 2 | ITEM 2.UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS | 670–672 | `block:198a707945b6bbcbc6b31b31e9cb3be0de77761803fbc4a95b5732b0a395ca6f` | `block:642589ec51c6ab1f437ecf1a8cb50297ab5f27ab8c8c55923cd85ed76f2b5591` |
| S10: classified; Part II, Item 5 | ITEM 5.OTHER INFORMATION | 673–678 | `block:d98f8f358b83d24d6663ce7347e182d34961b40c089ef7b0fc468826d53e9962` | `block:6cebe9ff1763d610de8427cf623fc0c253855c149f142c2f8713a9d246387f94` |
| S11: classified; Part II, Item 6 | ITEM 6.EXHIBITS | 679–686 | `block:a6e552d0644489cd4d5ae79e224cd1cae6d12116cb9415f7ed1cfd5b7fff882a` | `block:613f9c312fdfd5d15c365c9496d392e1dbae5bae211bcc4f3e6cfa47e14521b9` |
| S12: unclassified; Part unknown, Item none | SIGNATURES | 687–691 | `block:44142c7214d7123fb7baef8585605711baa4285afce4ca10477562acc2fa3714` | `block:30228aac1728d22019278139561777f2eb31b841d90fbaea636b981bdea878a9` |

### F18 — Alphabet — 0001652044-26-000071 — 10-Q

- Filing date **2026-07-23**; report date **2026-06-30**; split **held_out**; **822 blocks**, **13 detected ranges** (9 classified, 0 ambiguous, 4 unclassified).
- Document ID: `document:ed984e45281a25c4b2a86f724cbaecfde15ae1b8de5027b499b0143e18f14575`.
- Source: [goog-20260630.htm](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000071/goog-20260630.htm); [exact local HTML](../.runtime/artifacts/bronze/sha256/20/2066731bde8531eff1054fe178e85c701ec0eba3a18b9f309ee6945442ecad7a); 2,464,239 bytes; SHA-256 `2066731bde8531eff1054fe178e85c701ec0eba3a18b9f309ee6945442ecad7a`.
- Logical output SHA-256: `63ef5e6dc39bb1db99fa9bbfae6753103a40aec669e7bc926d55ecc63019d5cc`; stable replay/prior-run comparison **PASS**.
- Provenance **PASS**, **822/822** locators; fetch `446dc628-1152-4883-a096-afce12369210`; source links and section/block graph revalidated.
- Missing priority sections: **none**. Other undetected form labels (including ambiguity): II:3, II:4.
- Unclassified/ambiguous ranges: S0 0–48 (unclassified; Part unknown, Item none); S1 49–49 (unclassified; Part I, Item none); S6 758–758 (unclassified; Part II, Item none); S12 817–821 (unclassified; Part unknown, Item none).
- Parser warnings: `html_recovered` ×1, `toc_content_retained` ×1, `unclassified_content` ×1, `part_preamble` ×2, `non_item_section` ×1; total **6**. Parse errors **0**.

| Range / detected section | Source heading | Inclusive ordinals | Start block ID | End block ID |
| --- | --- | --- | --- | --- |
| S0: unclassified; Part unknown, Item none | [TABLE] | 0–48 | `block:7d8c1bd7ca98bf910f3745291c2153d9d643a33ab0850613e7d70d5559a78d09` | `block:c0ae61bf97c51de6c5129511efbca9e923095342650e1a117a7d0115b5e7a815` |
| S1: unclassified; Part I, Item none | PART I. FINANCIAL INFORMATION | 49–49 | `block:2932bc3d8f0d0600a156f20be57d6c19e07b5877c662db88da55ce0675665c56` | `block:2932bc3d8f0d0600a156f20be57d6c19e07b5877c662db88da55ce0675665c56` |
| S2: classified; Part I, Item 1 | ITEM 1.FINANCIAL STATEMENTS | 50–486 | `block:d58c9a6bd92fc9198cf91af0e7934da9ad4817cf37dc7c182f9c477c761a5eeb` | `block:291f5d5219fc1f46aa54a217348ac703140652ad2bc4bdda899266724388b364` |
| S3: classified; Part I, Item 2 | ITEM 2.MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS | 487–746 | `block:f00ee51fba3a55f6987ba80229a11fe9ed3e26de2c49d1033da333e75bebe27a` | `block:435530dc89deed1bc68c65842628b9bf738aeafb489ec2ec21c80657bd99a0c8` |
| S4: classified; Part I, Item 3 | ITEM 3.QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK | 747–748 | `block:460b836ca4a6656fcfced3fcdccba9a8f33dbb971393c4fd9d83efcbe1d10f1f` | `block:eaa922b425a461099c01fce631eb8ef66b2334b6a973e7093e506169e3b6b4bd` |
| S5: classified; Part I, Item 4 | ITEM 4.CONTROLS AND PROCEDURES | 749–757 | `block:ffbc681295be8e7cad3dfa049c0664079af4a3635db9666b43b9a3a60c45a42c` | `block:5fd911bbd63776e27577edca8c4052b34bb9e7e4ad967c198127b63dcab5ea7b` |
| S6: unclassified; Part II, Item none | PART II. OTHER INFORMATION | 758–758 | `block:f04100e6a32551d3d58be4dee7093e4856f2eb07b1a685f0fd16ad4f7b673d98` | `block:f04100e6a32551d3d58be4dee7093e4856f2eb07b1a685f0fd16ad4f7b673d98` |
| S7: classified; Part II, Item 1 | ITEM 1.LEGAL PROCEEDINGS | 759–760 | `block:3ee035d2a189e5cb98b13a8b7473ef61beb6fa324d54aa6e5ee2f44fe434ae5d` | `block:54ec673206cc3687716075e8b5241227717505e48d0eb499f485e036104e4e0e` |
| S8: classified; Part II, Item 1A | ITEM 1A.RISK FACTORS | 761–795 | `block:2669e56b851a228dc4e5076980151c8240756aae368411912ae1b628a80d275b` | `block:d74a978a1079055403b33454564b2199d82b8e79dcd369fbff12f4bdaa9d9c28` |
| S9: classified; Part II, Item 2 | ITEM 2.UNREGISTERED SALES OF EQUITY SECURITIES AND USE OF PROCEEDS | 796–800 | `block:56f9384f8163f43b9c8cc8160c4ad9676e58e72089e8cb46ece87ce7af939ade` | `block:79e8ec86ade73500f7c3988df8013e11793b563cf360d30bcd4189dd61c9c092` |
| S10: classified; Part II, Item 5 | ITEM 5.OTHER INFORMATION | 801–807 | `block:b0ba3f245741e93929fc0ebd1383372f4dbc93a091d90d5f059902bb237976bb` | `block:b5cf518514b214f7037300d65a6a6789847991920ce04fbe77cfcfd67927be86` |
| S11: classified; Part II, Item 6 | ITEM 6.EXHIBITS | 808–816 | `block:95a0826b97100edf156c3e7ef2624ce35ef21122018d2d7e4f31be8f5f0dbf19` | `block:5619e428f50f6c8b37a5b22054b8efe20d8667aabeb7811444d0c44ab150cb03` |
| S12: unclassified; Part unknown, Item none | SIGNATURES | 817–821 | `block:b112d1eab94dd72c65dd179a9c224db94e1fbdc592ab2918c5146962d7750b3c` | `block:c690b96982e0f168ab093648131c4d89876a28d533a2f14c3453db82a22d32cc` |

## Human-review sample packet

**50 distinct source locations**, across five companies and both 10-K/10-Q filings, including both JPMorgan quarters. Status for every sample: **prepared and source-inspected by the reviewing agent; NOT independently human-verified**. These are a purposeful diagnostic selection, not a randomized accuracy sample. A human can compare the source location and excerpt with the claimed physical section, record accept/reject/uncertain, and adjudicate disagreements. The existing 25 boundary labels are not relabeled by this packet.

Locators below give the exact numeric XPath in the recovered original DOM and half-open Unicode offsets in the normalized document representation identified by `text_sha256`. Offsets are **not raw HTML byte positions**. SEC fragment links use a nearby original ancestor ID when available; the exact XPath/local SHA-256 is authoritative for this review. Raw source files may be minified onto one line. Extracted text and source excerpts longer than the display limit end in `[…]`; the complete extracted block remains in the linked result JSON. Opaque tables correctly show `[TABLE]`, with source text shown separately for inspection.

Sample category counts: Section heading: 10, Table-of-contents candidate: 10, Narrative near financial tables: 10, Section transition: 5, End of document: 5, JPMorgan introduction heading in table: 2, JPMorgan MD&A narrative: 2, JPMorgan financial statement heading: 2, JPMorgan missing-part boundary: 2, JPMorgan Part II transition: 2.

### H01 — JPMorgan Chase & Co. 10-K — Section heading

- Document: **0001628280-26-008131**, `jpm-20251231.htm`; `document:a514e8bfa0c42823090ba32aa168d0e9a4e5c00b7167084673212ddf4620b956`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-008131.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/42/428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05), recovered source line 8; XPath `/*[1]/*[2]/*[45]`.
- Block **31**, kind **paragraph**; full block ID `block:65c9fd5eeeed08c617c0229132118fe690e365b3d0969ef9ea050df2f223f741`.
- Detected section **S2: classified; Part I, Item 1**; section ID `section:b7afc07958627cbb09e9e3f291fdefacda2e3e6181697d20f266fa8f3dca22ad`; source heading “Item 1. Business.”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[45]`; normalized offsets `[3484, 3501)`; `text_sha256=63255a0360a0e06c0e103586318eb849c1ddbfe8d83aacf9d4ec123c3f73c877`.
- Extracted text:

> Item 1. Business.

Why this matters: A short explicit item title starts this classified range; compare the original heading and the preceding content. This is an agent-inspected candidate for human adjudication.

Human disposition: **pending**.

### H02 — JPMorgan Chase & Co. 10-K — Table-of-contents candidate

- Document: **0001628280-26-008131**, `jpm-20251231.htm`; `document:a514e8bfa0c42823090ba32aa168d0e9a4e5c00b7167084673212ddf4620b956`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-008131.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/42/428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05), recovered source line 8; XPath `/*[1]/*[2]/*[38]/*[1]`.
- Block **29**, kind **table**; full block ID `block:9d9513d4e336d94985ffeaa68210ebc0a766f4bb30aa2559e73e1c823ccc02f1`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:7d3b4e05ce12d694da93a53d8aa8a707093d7444e10fb01e42d796f5c428763a`; source heading “UNITED STATES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[38]/*[1]`; normalized offsets `[3469, 3476)`; `text_sha256=63255a0360a0e06c0e103586318eb849c1ddbfe8d83aacf9d4ec123c3f73c877`.
- Extracted text:

> [TABLE]

Source element text for comparison (separate from extracted text):

> Part IPageItem 1.Business.1Overview1Business segments & Corporate1Competition1Supervision and regulation2-6Human capital7-8Distribution of assets, liabilities and stockholders’ equity; interest rates and interest differentials315-319Item 1A.Risk Factors.9-31Item 1B.Unresolved Staff Comments.32Item 1C.Cybersecurity.32Item 2.Properties.32Item 3.Legal Proceedings.32Item 4.Mine Safety Disclosures.32Part IIItem 5.Market for Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities.33Item 6.Reserved33Item 7.Management’s Discussion and Analysis of Financial Condition and Results of Operations.33Item 7A.Quantitative and Qualitative Disclosures About Market Risk.33Item 8.Financial […]

Why this matters: Navigation must remain available without becoming a body item boundary. For an opaque table the extracted text is deliberately [TABLE]; the adjacent source excerpt exposes the candidate labels for review.

Human disposition: **pending**.

### H03 — JPMorgan Chase & Co. 10-K — Narrative near financial tables

- Document: **0001628280-26-008131**, `jpm-20251231.htm`; `document:a514e8bfa0c42823090ba32aa168d0e9a4e5c00b7167084673212ddf4620b956`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-008131.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/42/428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05), recovered source line 8; XPath `/*[1]/*[2]/*[208]/*[1]/*[2]`.
- Block **839**, kind **paragraph**; full block ID `block:2a58cf4dd489431097e5b60acb5c34c05caecaf1d6b00282883de05dc27c48f4`.
- Detected section **S13: classified; Part II, Item 8**; section ID `section:5f0657c3608add6efe0fc1ced6ada6ccf9953261b1a9b1a854b6f1442cb34f0a`; source heading “Item 8. Financial Statements and Supplementary Data.”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[208]/*[1]/*[2]`; normalized offsets `[158655, 158902)`; `text_sha256=63255a0360a0e06c0e103586318eb849c1ddbfe8d83aacf9d4ec123c3f73c877`.
- Extracted text:

> The Consolidated Financial Statements, together with the Notes thereto and the report thereon dated February 13, 2026, of PricewaterhouseCoopers LLP, the Firm’s independent registered public accounting firm (PCAOB ID 238), appear on pages 162–314.

Why this matters: Checks narrative/table separation and section ownership around financial disclosure. Review the source table and nearby footnote or explanatory prose; no cell values or financial correctness are scored here.

Human disposition: **pending**.

### H04 — JPMorgan Chase & Co. 10-K — Section transition

- Document: **0001628280-26-008131**, `jpm-20251231.htm`; `document:a514e8bfa0c42823090ba32aa168d0e9a4e5c00b7167084673212ddf4620b956`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-008131.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/42/428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05), recovered source line 8; XPath `/*[1]/*[2]/*[97]/*[1]/*[1]`.
- Block **135**, kind **paragraph**; full block ID `block:d5040d438cdcf975c47c99a302acc28bf8f624e51cc560942b391a9534601a46`.
- Detected section **S3: classified; Part I, Item 1A**; section ID `section:e0ca29d387efca046bd90ec77fd31707549ef8abb3b585716325ea68f28d5f4e`; source heading “Item 1A. Risk Factors.”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[97]/*[1]/*[1]`; normalized offsets `[41948, 41970)`; `text_sha256=63255a0360a0e06c0e103586318eb849c1ddbfe8d83aacf9d4ec123c3f73c877`.
- Extracted text:

> Item 1A. Risk Factors.

Preceding block **134**, owned by **S2**: “[TABLE]”.

Why this matters: Tests the boundary from Business to Risk Factors. The immediately preceding block remains in the previous physical range; the new heading must start the next one.

Human disposition: **pending**.

### H05 — JPMorgan Chase & Co. 10-K — End of document

- Document: **0001628280-26-008131**, `jpm-20251231.htm`; `document:a514e8bfa0c42823090ba32aa168d0e9a4e5c00b7167084673212ddf4620b956`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-008131.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/42/428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05), recovered source line 8; XPath `/*[1]/*[2]/*[2006]/*[1]/*[1]/*[1]`.
- Block **4595**, kind **table**; full block ID `block:e597f6b41958d0a5dfb386c933e8d2e14425361cbd33d64e8a93d59944a0f278`.
- Detected section **S24: unclassified; Part unknown, Item none**; section ID `section:7f552157f6f81bae7d9be36d74ea7401e20ee81348e13ca99bcd48123135e9eb`; source heading “Signatures”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[2006]/*[1]/*[1]/*[1]`; normalized offsets `[911390, 911397)`; `text_sha256=63255a0360a0e06c0e103586318eb849c1ddbfe8d83aacf9d4ec123c3f73c877`.
- Extracted text:

> [TABLE]

Source element text for comparison (separate from extracted text):

> 328JPMorgan Chase & Co./2025 Form 10-K

Why this matters: Confirms that the final emitted block remains source-linked and owned. An annual filing may place substantial annex or report content after signatures; this is physical ownership rather than resolved incorporation by reference.

Human disposition: **pending**.

### H06 — JPMorgan Chase & Co. 10-Q — Section heading

- Document: **0001628280-26-029344**, `jpm-20260331.htm`; `document:3150c4203a3994c1a0a4b2d65550a0a25942c608f619840f0234683a77756351`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-029344.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026029344/jpm-20260331.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/19/19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc), recovered source line 8; XPath `/*[1]/*[2]/*[1135]/*[1]/*[10]`.
- Block **2240**, kind **paragraph**; full block ID `block:9fc5942dd049456f333df976ae5a28f66d09746cbee4e4cbefc4426f381bc518`.
- Detected section **S4: classified; Part II, Item 1**; section ID `section:966c700cb82b553941e041431c73e3c59ece09d1d7417042e110f93187ab4e30`; source heading “Item 1. Legal Proceedings.”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[1135]/*[1]/*[10]`; normalized offsets `[379452, 379478)`; `text_sha256=1af0d153598ad2f111296aedd6e822b0c13cd821bb761246fade60a9e35bcad5`.
- Extracted text:

> Item 1. Legal Proceedings.

Why this matters: A short explicit item title starts this classified range; compare the original heading and the preceding content. This is an agent-inspected candidate for human adjudication.

Human disposition: **pending**.

### H07 — JPMorgan Chase & Co. 10-Q — Table-of-contents candidate

- Document: **0001628280-26-029344**, `jpm-20260331.htm`; `document:3150c4203a3994c1a0a4b2d65550a0a25942c608f619840f0234683a77756351`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-029344.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026029344/jpm-20260331.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/19/19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc), recovered source line 8; XPath `/*[1]/*[2]/*[33]/*[3]/*[1]/*[1]`.
- Block **25**, kind **table**; full block ID `block:eab01a8061798b7930128dd882700cb73f3f93696bb1643d5e8f0393e0b56f42`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:6debeda1ccc014e10ebf1fe1f121df47058e76cd854f8dc7e6603d5a8eb213d8`; source heading “UNITED STATES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[33]/*[3]/*[1]/*[1]`; normalized offsets `[1686, 1693)`; `text_sha256=1af0d153598ad2f111296aedd6e822b0c13cd821bb761246fade60a9e35bcad5`.
- Extracted text:

> [TABLE]

Source element text for comparison (separate from extracted text):

> PageReport of Independent Registered Public Accounting Firm168Consolidated Average Balance Sheets, Interest and Rates (unaudited) for the three months ended March 31, 2026 and 2025169Glossary of Terms and Acronyms and Line of Business Metrics170Item 2.Management’s Discussion and Analysis of Financial Condition and Results of Operations.Consolidated Financial Highlights3Introduction4Executive Overview5Consolidated Results of Operations9Consolidated Balance Sheets and Cash Flows Analysis12Explanation and Reconciliation of the Firm’s Use of Non-GAAP Financial Measures15Business Segment & Corporate Results17Firmwide Risk Management32Capital Risk Management33Liquidity Risk Management41Consumer Credit Portfolio50Whol […]

Why this matters: Navigation must remain available without becoming a body item boundary. For an opaque table the extracted text is deliberately [TABLE]; the adjacent source excerpt exposes the candidate labels for review.

Human disposition: **pending**.

### H08 — JPMorgan Chase & Co. 10-Q — Narrative near financial tables

- Document: **0001628280-26-029344**, `jpm-20260331.htm`; `document:3150c4203a3994c1a0a4b2d65550a0a25942c608f619840f0234683a77756351`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-029344.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026029344/jpm-20260331.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/19/19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc), recovered source line 8; XPath `/*[1]/*[2]/*[609]`.
- Block **1025**, kind **paragraph**; full block ID `block:94e204964dcb84de2141d448324a4de1838fbf23f2d69e7556ba955f42381dfe`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:6debeda1ccc014e10ebf1fe1f121df47058e76cd854f8dc7e6603d5a8eb213d8`; source heading “UNITED STATES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[609]`; normalized offsets `[173486, 173586)`; `text_sha256=1af0d153598ad2f111296aedd6e822b0c13cd821bb761246fade60a9e35bcad5`.
- Extracted text:

> The Notes to Consolidated Financial Statements (unaudited) are an integral part of these statements.

Adjacent opaque table: block **1024**, `block:a53904f3a6dc4a62bf3efeff76f7f9f806cf2b02c11cf40f5d7bf9cd2aeb90a9`, source XPath `/*[1]/*[2]/*[608]/*[1]`.

Why this matters: Checks narrative/table separation and section ownership around financial disclosure. Review the source table and nearby footnote or explanatory prose; no cell values or financial correctness are scored here.

Human disposition: **pending**.

### H09 — Apple 10-K — Section heading

- Document: **0000320193-24-000123**, `aapl-20240928.htm`; `document:9c890c6cc0d4352c58b9ea63d872692317047aa7e9f10661b3203752969d64b0`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0000320193-24-000123.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/87/87811e303e632b0f1843b9bc161c1b3af9c501ffec0a51a9825cc796dc369dcf), recovered source line 8; XPath `/*[1]/*[2]/*[72]`.
- Block **55**, kind **heading**; full block ID `block:7817d263c11f8c51e341ab836544624d8eb131acccc535f729d88385c7d49f01`.
- Detected section **S2: classified; Part I, Item 1**; section ID `section:11319c9122894dbadd88703c52ab31a1cef9ff8bfcd6a49771a707abc3dd77f0`; source heading “Item 1. Business”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[72]`; normalized offsets `[6442, 6458)`; `text_sha256=47c62c77d665410023cc506bedb1120358e1072512c63dbc53256198481d0b56`.
- Extracted text:

> Item 1. Business

Why this matters: A short explicit item title starts this classified range; compare the original heading and the preceding content. This is an agent-inspected candidate for human adjudication.

Human disposition: **pending**.

### H10 — Apple 10-K — Table-of-contents candidate

- Document: **0000320193-24-000123**, `aapl-20240928.htm`; `document:9c890c6cc0d4352c58b9ea63d872692317047aa7e9f10661b3203752969d64b0`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0000320193-24-000123.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/87/87811e303e632b0f1843b9bc161c1b3af9c501ffec0a51a9825cc796dc369dcf), recovered source line 8; XPath `/*[1]/*[2]/*[63]/*[1]`.
- Block **51**, kind **table**; full block ID `block:66f1174dd1dc28c2f45cfa586c15525c2726d5fdeb5154931474d9f6c6d83f9a`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:d00991b9d744b60cf53f99dcb3bb2c708a3f7fe88faa935a9a91c6eceb618000`; source heading “[TABLE]”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[63]/*[1]`; normalized offsets `[4443, 4450)`; `text_sha256=47c62c77d665410023cc506bedb1120358e1072512c63dbc53256198481d0b56`.
- Extracted text:

> [TABLE]

Source element text for comparison (separate from extracted text):

> PagePart IItem 1.Business1Item 1A.Risk Factors5Item 1B.Unresolved Staff Comments17Item 1C.Cybersecurity17Item 2.Properties18Item 3.Legal Proceedings18Item 4.Mine Safety Disclosures18Part IIItem 5.Market for Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities19Item 6.[Reserved]20Item 7.Management’s Discussion and Analysis of Financial Condition and Results of Operations21Item 7A.Quantitative and Qualitative Disclosures About Market Risk27Item 8.Financial Statements and Supplementary Data28Item 9.Changes in and Disagreements with Accountants on Accounting and Financial Disclosure51Item 9A.Controls and Procedures51Item 9B.Other Information52Item 9C.Disclosure Regarding […]

Why this matters: Navigation must remain available without becoming a body item boundary. For an opaque table the extracted text is deliberately [TABLE]; the adjacent source excerpt exposes the candidate labels for review.

Human disposition: **pending**.

### H11 — Apple 10-K — Narrative near financial tables

- Document: **0000320193-24-000123**, `aapl-20240928.htm`; `document:9c890c6cc0d4352c58b9ea63d872692317047aa7e9f10661b3203752969d64b0`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0000320193-24-000123.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/87/87811e303e632b0f1843b9bc161c1b3af9c501ffec0a51a9825cc796dc369dcf), recovered source line 8; XPath `/*[1]/*[2]/*[534]`.
- Block **407**, kind **paragraph**; full block ID `block:dc4296a91bf3375ff5841dd1f1cee56760977a09b403a6d8294c9d6f5e0f0391`.
- Detected section **S14: classified; Part II, Item 8**; section ID `section:2533b4f6d0235e9efa7950d8d53a093249012c897e8468b93c5a21bf412dc372`; source heading “Item 8. Financial Statements and Supplementary Data”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[534]`; normalized offsets `[117183, 117476)`; `text_sha256=47c62c77d665410023cc506bedb1120358e1072512c63dbc53256198481d0b56`.
- Extracted text:

> All financial statement schedules have been omitted, since the required information is not applicable or is not present in amounts sufficient to require submission of the schedule, or because the information required is included in the consolidated financial statements and accompanying notes.

Adjacent opaque table: block **406**, `block:a34cd20c2068a5f1a1121e8dc20ea962d196dd75f23452526f90833f064c7564`, source XPath `/*[1]/*[2]/*[533]/*[1]`.

Why this matters: Checks narrative/table separation and section ownership around financial disclosure. Review the source table and nearby footnote or explanatory prose; no cell values or financial correctness are scored here.

Human disposition: **pending**.

### H12 — Apple 10-K — Section transition

- Document: **0000320193-24-000123**, `aapl-20240928.htm`; `document:9c890c6cc0d4352c58b9ea63d872692317047aa7e9f10661b3203752969d64b0`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0000320193-24-000123.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/87/87811e303e632b0f1843b9bc161c1b3af9c501ffec0a51a9825cc796dc369dcf), recovered source line 8; XPath `/*[1]/*[2]/*[159]`.
- Block **121**, kind **heading**; full block ID `block:bc692c3848060f6bba54da6c23ffb8f0ef3546940b44d5116105e7d5447c0bc0`.
- Detected section **S3: classified; Part I, Item 1A**; section ID `section:3518ff6ca7523d952a6e5437173be7bd682859011d5fc84626096b822c0d881c`; source heading “Item 1A. Risk Factors”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[159]`; normalized offsets `[22142, 22163)`; `text_sha256=47c62c77d665410023cc506bedb1120358e1072512c63dbc53256198481d0b56`.
- Extracted text:

> Item 1A. Risk Factors

Preceding block **120**, owned by **S2**: “The Company’s Annual Reports on Form 10-K, Quarterly Reports on Form 10-Q, Current Reports on Form 8-K, and amendments to reports filed pursuant to Sections 13(a) and 15(d) of the Securities Exchange  […]”.

Why this matters: Tests the boundary from Business to Risk Factors. The immediately preceding block remains in the previous physical range; the new heading must start the next one.

Human disposition: **pending**.

### H13 — Apple 10-K — End of document

- Document: **0000320193-24-000123**, `aapl-20240928.htm`; `document:9c890c6cc0d4352c58b9ea63d872692317047aa7e9f10661b3203752969d64b0`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0000320193-24-000123.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/87/87811e303e632b0f1843b9bc161c1b3af9c501ffec0a51a9825cc796dc369dcf), recovered source line 8; XPath `/*[1]/*[2]/*[820]/*[1]/*[1]`.
- Block **716**, kind **paragraph**; full block ID `block:080554494a41961469ee8c7b45dffbafc3a51183937700d0e9a048a725569efa`.
- Detected section **S28: unclassified; Part unknown, Item none**; section ID `section:a0ea005168cb4ad9134d723472064c99739fea93ef25e55bd0f3920d3a14f6c2`; source heading “SIGNATURES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[820]/*[1]/*[1]`; normalized offsets `[168060, 168092)`; `text_sha256=47c62c77d665410023cc506bedb1120358e1072512c63dbc53256198481d0b56`.
- Extracted text:

> Apple Inc. | 2024 Form 10-K | 57

Why this matters: Confirms that the final emitted block remains source-linked and owned. An annual filing may place substantial annex or report content after signatures; this is physical ownership rather than resolved incorporation by reference.

Human disposition: **pending**.

### H14 — Apple 10-Q — Section heading

- Document: **0000320193-26-000013**, `aapl-20260328.htm`; `document:1a23eae96fc36db7bdb13d5c9d4ba598f41bf8b60bdd03d2e25c8a9620e97b82`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0000320193-26-000013.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/7d/7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91), recovered source line 8; XPath `/*[1]/*[2]/*[58]`.
- Block **42**, kind **heading**; full block ID `block:0d6e966362da73cdc8e11ead91115d70c74b585b7c4f74e1232af3c03713f026`.
- Detected section **S2: classified; Part I, Item 1**; section ID `section:705095432e73560d44b13dd1c1081d5e30f5195cb0eee3b6acc668398c7876eb`; source heading “Item 1. Financial Statements”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[58]`; normalized offsets `[2286, 2314)`; `text_sha256=ee8d12d9d37c0184798d970faf89b5b1639ec35df45f4887ed6af6f34b7162b6`.
- Extracted text:

> Item 1. Financial Statements

Why this matters: A short explicit item title starts this classified range; compare the original heading and the preceding content. This is an agent-inspected candidate for human adjudication.

Human disposition: **pending**.

### H15 — Apple 10-Q — Table-of-contents candidate

- Document: **0000320193-26-000013**, `aapl-20260328.htm`; `document:1a23eae96fc36db7bdb13d5c9d4ba598f41bf8b60bdd03d2e25c8a9620e97b82`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0000320193-26-000013.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/7d/7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91), recovered source line 8; XPath `/*[1]/*[2]/*[51]/*[1]`.
- Block **40**, kind **table**; full block ID `block:e7223aee761a1cbfed4e81d367e34b6eba06a1b19bf121c9390d131b22a6cfdd`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:bc2ff9e5fa10b7eaf4a998912fc03af92ee699de549e8796412fb0209f003b0b`; source heading “[TABLE]”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[51]/*[1]`; normalized offsets `[2247, 2254)`; `text_sha256=ee8d12d9d37c0184798d970faf89b5b1639ec35df45f4887ed6af6f34b7162b6`.
- Extracted text:

> [TABLE]

Source element text for comparison (separate from extracted text):

> PagePart IItem 1.Financial Statements1Item 2.Management’s Discussion and Analysis of Financial Condition and Results of Operations13Item 3.Quantitative and Qualitative Disclosures About Market Risk19Item 4.Controls and Procedures19Part IIItem 1.Legal Proceedings20Item 1A.Risk Factors21Item 2.Unregistered Sales of Equity Securities and Use of Proceeds24Item 3.Defaults Upon Senior Securities25Item 4.Mine Safety Disclosures25Item 5.Other Information25Item 6.Exhibits25

Why this matters: Navigation must remain available without becoming a body item boundary. For an opaque table the extracted text is deliberately [TABLE]; the adjacent source excerpt exposes the candidate labels for review.

Human disposition: **pending**.

### H16 — Apple 10-Q — Narrative near financial tables

- Document: **0000320193-26-000013**, `aapl-20260328.htm`; `document:1a23eae96fc36db7bdb13d5c9d4ba598f41bf8b60bdd03d2e25c8a9620e97b82`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0000320193-26-000013.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/7d/7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91), recovered source line 8; XPath `/*[1]/*[2]/*[62]`.
- Block **45**, kind **paragraph**; full block ID `block:78e24d818a71965a115206759caa4a3cadc38eb4031048623137c0dea49699ee`.
- Detected section **S2: classified; Part I, Item 1**; section ID `section:705095432e73560d44b13dd1c1081d5e30f5195cb0eee3b6acc668398c7876eb`; source heading “Item 1. Financial Statements”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[62]`; normalized offsets `[2386, 2481)`; `text_sha256=ee8d12d9d37c0184798d970faf89b5b1639ec35df45f4887ed6af6f34b7162b6`.
- Extracted text:

> (In millions, except number of shares, which are reflected in thousands, and per-share amounts)

Adjacent opaque table: block **46**, `block:e117978347886c18634d6b9b88c8fa48762258956d5a805b034b0c3df7a202f1`, source XPath `/*[1]/*[2]/*[64]/*[1]`.

Why this matters: Checks narrative/table separation and section ownership around financial disclosure. Review the source table and nearby footnote or explanatory prose; no cell values or financial correctness are scored here.

Human disposition: **pending**.

### H17 — Microsoft 10-K — Section heading

- Document: **0000950170-25-100235**, `msft-20250630.htm`; `document:011f513a22ff4c7d01d4d87e034b08787d9a778ad7a5d7cde1c5d0997367794d`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0000950170-25-100235.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm#item_1_business); [exact local bytes](../.runtime/artifacts/bronze/sha256/bd/bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665), recovered source line 715; XPath `/*[1]/*[2]/*[11]/*[4]`.
- Block **38**, kind **heading**; full block ID `block:5e9c10ebb4d0f9a98d70182da242028fee73feeb932427ebef5d0ea6962fdaef`.
- Detected section **S2: classified; Part I, Item 1**; section ID `section:52e4adcf5e3c46d781e85eaabf57e7f4145da6a4dcfbc034176243af15fa153f`; source heading “ITEM 1. BUSINESS”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[11]/*[4]`; normalized offsets `[5196, 5212)`; `text_sha256=ad5da49ac6a5375335900543590b5063dd9e8ea31a629c437e099b81638372b4`.
- Extracted text:

> ITEM 1. BUSINESS

Why this matters: A short explicit item title starts this classified range; compare the original heading and the preceding content. This is an agent-inspected candidate for human adjudication.

Human disposition: **pending**.

### H18 — Microsoft 10-K — Table-of-contents candidate

- Document: **0000950170-25-100235**, `msft-20250630.htm`; `document:011f513a22ff4c7d01d4d87e034b08787d9a778ad7a5d7cde1c5d0997367794d`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0000950170-25-100235.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/bd/bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665), recovered source line 194; XPath `/*[1]/*[2]/*[7]/*[6]`.
- Block **31**, kind **table**; full block ID `block:b1937142047964f48dd4d8011bfd22c42e41abc927cfcb663a28dae74179a974`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:1cec7e4c3d5eacae6e2b1c0aa1d7df4db7632f2e19366795822094d56cd16fe0`; source heading “UNITED STATES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[7]/*[6]`; normalized offsets `[3401, 3408)`; `text_sha256=ad5da49ac6a5375335900543590b5063dd9e8ea31a629c437e099b81638372b4`.
- Extracted text:

> [TABLE]

Source element text for comparison (separate from extracted text):

> Page PART I Item 1. Business 3 Information about our Executive Officers 14 Item 1A. Risk Factors 16 Item 1B. Unresolved Staff Comments 30 Item 1C. Cybersecurity 30 Item 2. Properties 32 Item 3. Legal Proceedings 32 Item 4. Mine Safety Disclosures 32 PART II Item 5. Market for Registrant’s Common Equity, Related Stockholder Matters, and Issuer Purchases of Equity Securities 33 Item 6. [Reserved] 34 Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations 35 Item 7A. Quantitative and Qualitative Disclosures About Market Risk 49 Item 8. Financial Statements and Supplementary Data 50 Item 9. Changes in and Disagreements with Accountants on Accounting and Financial Disclosure 89  […]

Why this matters: Navigation must remain available without becoming a body item boundary. For an opaque table the extracted text is deliberately [TABLE]; the adjacent source excerpt exposes the candidate labels for review.

Human disposition: **pending**.

### H19 — Microsoft 10-K — Narrative near financial tables

- Document: **0000950170-25-100235**, `msft-20250630.htm`; `document:011f513a22ff4c7d01d4d87e034b08787d9a778ad7a5d7cde1c5d0997367794d`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0000950170-25-100235.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm#F_cd60e08d-5d70-4675-a064-8ef989dfa3fa); [exact local bytes](../.runtime/artifacts/bronze/sha256/bd/bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665), recovered source line 6570; XPath `/*[1]/*[2]/*[247]/*[2]/*[1]/*[5]`.
- Block **931**, kind **paragraph**; full block ID `block:fef2a298186a26dac6af78411940a2bf9c8886c93f1dd8c5e3125bdc6c7c16a9`.
- Detected section **S14: classified; Part II, Item 8**; section ID `section:8741d04ae0a58cb5fb66f84dcfc2058a0057b1b07c8e4eba54502df46982805d`; source heading “ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[247]/*[2]/*[1]/*[5]`; normalized offsets `[211283, 211407)`; `text_sha256=ad5da49ac6a5375335900543590b5063dd9e8ea31a629c437e099b81638372b4`.
- Extracted text:

> Anti-dilutive stock-based awards excluded from the calculations of diluted EPS were immaterial during the periods presented.

Adjacent opaque table: block **930**, `block:6befb02d4c540d113daa75bb526c485454cddc71670546d57232419e7dbbddcc`, source XPath `/*[1]/*[2]/*[247]/*[2]/*[1]/*[3]/*[1]/*[3]`.

Why this matters: Checks narrative/table separation and section ownership around financial disclosure. Review the source table and nearby footnote or explanatory prose; no cell values or financial correctness are scored here.

Human disposition: **pending**.

### H20 — Microsoft 10-K — Section transition

- Document: **0000950170-25-100235**, `msft-20250630.htm`; `document:011f513a22ff4c7d01d4d87e034b08787d9a778ad7a5d7cde1c5d0997367794d`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0000950170-25-100235.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm#item_1a_risk_factors); [exact local bytes](../.runtime/artifacts/bronze/sha256/bd/bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665), recovered source line 860; XPath `/*[1]/*[2]/*[63]/*[1]`.
- Block **285**, kind **heading**; full block ID `block:60ec0a8cc5a01879719f9c15db17511a502c85804edc5d9284c2abbb8722f950`.
- Detected section **S3: classified; Part I, Item 1A**; section ID `section:b644b20a47cf4835a52ffdb62208e76e065adf5b7a7448a7cf3e59ec027af034`; source heading “ITEM 1A. RISK FACTORS”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[63]/*[1]`; normalized offsets `[53358, 53379)`; `text_sha256=ad5da49ac6a5375335900543590b5063dd9e8ea31a629c437e099b81638372b4`.
- Extracted text:

> ITEM 1A. RISK FACTORS

Preceding block **284**, owned by **S2**: “Item 1A”.

Why this matters: Tests the boundary from Business to Risk Factors. The immediately preceding block remains in the previous physical range; the new heading must start the next one.

Human disposition: **pending**.

### H21 — Microsoft 10-K — End of document

- Document: **0000950170-25-100235**, `msft-20250630.htm`; `document:011f513a22ff4c7d01d4d87e034b08787d9a778ad7a5d7cde1c5d0997367794d`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0000950170-25-100235.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/bd/bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665), recovered source line 23004; XPath `/*[1]/*[2]/*[404]/*[1]`.
- Block **1400**, kind **paragraph**; full block ID `block:160f8a93703e77ab03a33a005d25b00ae0a720822d04c7c68af331afd9422510`.
- Detected section **S28: unclassified; Part unknown, Item none**; section ID `section:02803c715ae4acb2f8f538067f7af12506b899d20f1d8a3a37d61fdbc4c4a5dc`; source heading “SIGNATURES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[404]/*[1]`; normalized offsets `[264582, 264585)`; `text_sha256=ad5da49ac6a5375335900543590b5063dd9e8ea31a629c437e099b81638372b4`.
- Extracted text:

> 101

Why this matters: Confirms that the final emitted block remains source-linked and owned. An annual filing may place substantial annex or report content after signatures; this is physical ownership rather than resolved incorporation by reference.

Human disposition: **pending**.

### H22 — Microsoft 10-Q — Section heading

- Document: **0001193125-26-027207**, `msft-20251231.htm`; `document:ea322da70fcd6fd0e69ab7f893f045d092e2c423e108ac64d1d505da38d96ca6`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001193125-26-027207.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/789019/000119312526027207/msft-20251231.htm#item_1_financial_statements); [exact local bytes](../.runtime/artifacts/bronze/sha256/13/13b6006248fb7d5f3dfebb5425e6645a8ca4f8e1a438fe1c75a0578be13b2773), recovered source line 444; XPath `/*[1]/*[2]/*[11]/*[2]`.
- Block **29**, kind **heading**; full block ID `block:334e71455f195af60eec77682b89dfc2397300ffd42883630daabb45cf2589d4`.
- Detected section **S2: classified; Part I, Item 1**; section ID `section:79610fe3c20e0427608539e21438cdcf878a3cd58dd555c5d4cd4f2b164c0844`; source heading “ITEM 1. FINANCIAL STATEMENTS”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[11]/*[2]`; normalized offsets `[1928, 1956)`; `text_sha256=e43d136379fc9e47a24754cb2af979b05a127a0b1ce6678bb194237eb70f2de8`.
- Extracted text:

> ITEM 1. FINANCIAL STATEMENTS

Why this matters: A short explicit item title starts this classified range; compare the original heading and the preceding content. This is an agent-inspected candidate for human adjudication.

Human disposition: **pending**.

### H23 — Microsoft 10-Q — Table-of-contents candidate

- Document: **0001193125-26-027207**, `msft-20251231.htm`; `document:ea322da70fcd6fd0e69ab7f893f045d092e2c423e108ac64d1d505da38d96ca6`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001193125-26-027207.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/789019/000119312526027207/msft-20251231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/13/13b6006248fb7d5f3dfebb5425e6645a8ca4f8e1a438fe1c75a0578be13b2773), recovered source line 186; XPath `/*[1]/*[2]/*[7]/*[6]`.
- Block **24**, kind **table**; full block ID `block:c1a47a5e1f216e74fa99a51bbfb57a96c8d5c8d8b157bfb6db9e629b5a6632d1`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:3a340a9a56b25e2ececa6d22a7680561457f909f80721e6271385ce6101e64c5`; source heading “UNITED STATES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[7]/*[6]`; normalized offsets `[1874, 1881)`; `text_sha256=e43d136379fc9e47a24754cb2af979b05a127a0b1ce6678bb194237eb70f2de8`.
- Extracted text:

> [TABLE]

Source element text for comparison (separate from extracted text):

> Page PART I. FINANCIAL INFORMATION Item 1. Financial Statements a) Income Statements for the Three and Six Months Ended December 31, 2025 and 2024 3 b) Comprehensive Income Statements for the Three and Six Months Ended December 31, 2025 and 2024 4 c) Balance Sheets as of December 31, 2025 and June 30, 2025 5 d) Cash Flows Statements for the Three and Six Months Ended December 31, 2025 and 2024 6 e) Stockholders’ Equity Statements for the Three and Six Months Ended December 31, 2025 and 2024 7 f) Notes to Financial Statements 8 g) Report of Independent Registered Public Accounting Firm 29 Item 2. Management’s Discussion and Analysis of Financial Condition and Results of Operations 30 Item 3. Quantitative and Qua […]

Why this matters: Navigation must remain available without becoming a body item boundary. For an opaque table the extracted text is deliberately [TABLE]; the adjacent source excerpt exposes the candidate labels for review.

Human disposition: **pending**.

### H24 — Microsoft 10-Q — Narrative near financial tables

- Document: **0001193125-26-027207**, `msft-20251231.htm`; `document:ea322da70fcd6fd0e69ab7f893f045d092e2c423e108ac64d1d505da38d96ca6`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001193125-26-027207.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/789019/000119312526027207/msft-20251231.htm#F_16282753-ca19-4c69-ac74-8cfe2fdc385b); [exact local bytes](../.runtime/artifacts/bronze/sha256/13/13b6006248fb7d5f3dfebb5425e6645a8ca4f8e1a438fe1c75a0578be13b2773), recovered source line 4427; XPath `/*[1]/*[2]/*[43]/*[2]/*[1]/*[5]`.
- Block **115**, kind **paragraph**; full block ID `block:2e515147a18099b838b7e0bf21baa211a887e9f4e8dd98fde5eed32ab62f720d`.
- Detected section **S2: classified; Part I, Item 1**; section ID `section:79610fe3c20e0427608539e21438cdcf878a3cd58dd555c5d4cd4f2b164c0844`; source heading “ITEM 1. FINANCIAL STATEMENTS”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[43]/*[2]/*[1]/*[5]`; normalized offsets `[16663, 16787)`; `text_sha256=e43d136379fc9e47a24754cb2af979b05a127a0b1ce6678bb194237eb70f2de8`.
- Extracted text:

> Anti-dilutive stock-based awards excluded from the calculations of diluted EPS were immaterial during the periods presented.

Adjacent opaque table: block **114**, `block:1e9780449611ae2c277eb93d7b6f9d55a1b9abf49e88c56ccbb54e07e33a5494`, source XPath `/*[1]/*[2]/*[43]/*[2]/*[1]/*[3]/*[1]/*[3]`.

Why this matters: Checks narrative/table separation and section ownership around financial disclosure. Review the source table and nearby footnote or explanatory prose; no cell values or financial correctness are scored here.

Human disposition: **pending**.

### H25 — Amazon 10-K — Section heading

- Document: **0001018724-26-000004**, `amzn-20251231.htm`; `document:a938656a32a3ca28b99ce173af41ad362350fd609215aec8b61fc2e8f1d548e8`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001018724-26-000004.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/a2/a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35), recovered source line 8; XPath `/*[1]/*[2]/*[64]/*[1]`.
- Block **54**, kind **heading**; full block ID `block:d86e45cb07839b502658b5d065132611aa1ceffca686a3882e8bdd7b5d4dd23a`.
- Detected section **S2: classified; Part I, Item 1**; section ID `section:abb4cf0354f3aeca1ebab26860e6e0694bf48ad55647453aa32381acaccedaed`; source heading “Item 1. Business”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[64]/*[1]`; normalized offsets `[3936, 3952)`; `text_sha256=2b03e54aed7274d7c3503a00564f9017bf2627ca47d955397157d1b39148ee11`.
- Extracted text:

> Item 1. Business

Source element text for comparison (separate from extracted text):

> Item 1.Business

Why this matters: A short explicit item title starts this classified range; compare the original heading and the preceding content. This is an agent-inspected candidate for human adjudication.

Human disposition: **pending**.

### H26 — Amazon 10-K — Table-of-contents candidate

- Document: **0001018724-26-000004**, `amzn-20251231.htm`; `document:a938656a32a3ca28b99ce173af41ad362350fd609215aec8b61fc2e8f1d548e8`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001018724-26-000004.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/a2/a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35), recovered source line 8; XPath `/*[1]/*[2]/*[56]/*[1]`.
- Block **49**, kind **table**; full block ID `block:e9ad0b97c32f120485ffe69afd8059787f5f97ec53c8fbd8a80be0e384e58be6`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:69aa284e5199c435808b276174c0669acab040e4cde30f9f4ce8e7c8f8fbe691`; source heading “Table of Contents”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[56]/*[1]`; normalized offsets `[3884, 3891)`; `text_sha256=2b03e54aed7274d7c3503a00564f9017bf2627ca47d955397157d1b39148ee11`.
- Extracted text:

> [TABLE]

Source element text for comparison (separate from extracted text):

> PagePART IItem 1.Business3Item 1A.Risk Factors6Item 1B.Unresolved Staff Comments17Item 1C.Cybersecurity17Item 2.Properties18Item 3.Legal Proceedings18Item 4.Mine Safety Disclosures18PART IIItem 5.Market for the Registrant’s Common Stock, Related Shareholder Matters, and Issuer Purchases of Equity Securities19Item 6.Reserved19Item 7.Management’s Discussion and Analysis of Financial Condition and Results of Operations20Item 7A.Quantitative and Qualitative Disclosures About Market Risk31Item 8.Financial Statements and Supplementary Data33Item 9.Changes in and Disagreements with Accountants on Accounting and Financial Disclosure72Item 9A.Controls and Procedures72Item 9B.Other Information74Item 9C.Disclosure Regardi […]

Why this matters: Navigation must remain available without becoming a body item boundary. For an opaque table the extracted text is deliberately [TABLE]; the adjacent source excerpt exposes the candidate labels for review.

Human disposition: **pending**.

### H27 — Amazon 10-K — Narrative near financial tables

- Document: **0001018724-26-000004**, `amzn-20251231.htm`; `document:a938656a32a3ca28b99ce173af41ad362350fd609215aec8b61fc2e8f1d548e8`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001018724-26-000004.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/a2/a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35), recovered source line 8; XPath `/*[1]/*[2]/*[566]`.
- Block **490**, kind **paragraph**; full block ID `block:dda94651c4de80c2e300a49c5a8a64760861fa73f14dcd65b9803914c9f5ca75`.
- Detected section **S14: classified; Part II, Item 8**; section ID `section:8b5f37e80c0b8291531be42d838d4d8d51ffa08e5279b9a6e017a30b92e275c2`; source heading “Item 8. Financial Statements and Supplementary Data”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[566]`; normalized offsets `[135698, 135758)`; `text_sha256=2b03e54aed7274d7c3503a00564f9017bf2627ca47d955397157d1b39148ee11`.
- Extracted text:

> See accompanying notes to consolidated financial statements.

Adjacent opaque table: block **489**, `block:f22b643b96d21030dafaa680036d24de1457ef72117d2c7be838317586f57bd9`, source XPath `/*[1]/*[2]/*[565]/*[1]`.

Why this matters: Checks narrative/table separation and section ownership around financial disclosure. Review the source table and nearby footnote or explanatory prose; no cell values or financial correctness are scored here.

Human disposition: **pending**.

### H28 — Amazon 10-K — Section transition

- Document: **0001018724-26-000004**, `amzn-20251231.htm`; `document:a938656a32a3ca28b99ce173af41ad362350fd609215aec8b61fc2e8f1d548e8`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001018724-26-000004.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/a2/a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35), recovered source line 8; XPath `/*[1]/*[2]/*[114]/*[1]`.
- Block **100**, kind **heading**; full block ID `block:69673055da749dde4eaac3389afdd0f9c9089a4200bec48af6131c6eedfd8a44`.
- Detected section **S3: classified; Part I, Item 1A**; section ID `section:9737aeed331a9b533f2080b3b73e83466fc3c41597747f97c2097b632a644364`; source heading “Item 1A. Risk Factors”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[114]/*[1]`; normalized offsets `[16250, 16271)`; `text_sha256=2b03e54aed7274d7c3503a00564f9017bf2627ca47d955397157d1b39148ee11`.
- Extracted text:

> Item 1A. Risk Factors

Source element text for comparison (separate from extracted text):

> Item 1A.Risk Factors

Preceding block **99**, owned by **S2**: “[TABLE]”.

Why this matters: Tests the boundary from Business to Risk Factors. The immediately preceding block remains in the previous physical range; the new heading must start the next one.

Human disposition: **pending**.

### H29 — Amazon 10-K — End of document

- Document: **0001018724-26-000004**, `amzn-20251231.htm`; `document:a938656a32a3ca28b99ce173af41ad362350fd609215aec8b61fc2e8f1d548e8`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001018724-26-000004.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/a2/a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35), recovered source line 8; XPath `/*[1]/*[2]/*[974]/*[1]/*[1]`.
- Block **1016**, kind **paragraph**; full block ID `block:8431f3aa3b1878459ffc3f921caa7ae4cc2c762396e930b88ff1386900cbece1`.
- Detected section **S28: unclassified; Part unknown, Item none**; section ID `section:7ea5d2088af56a5e432f0bb577dd1f34b70707946b751f74cd103945ef0cd06b`; source heading “SIGNATURES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[974]/*[1]/*[1]`; normalized offsets `[242626, 242628)`; `text_sha256=2b03e54aed7274d7c3503a00564f9017bf2627ca47d955397157d1b39148ee11`.
- Extracted text:

> 79

Why this matters: Confirms that the final emitted block remains source-linked and owned. An annual filing may place substantial annex or report content after signatures; this is physical ownership rather than resolved incorporation by reference.

Human disposition: **pending**.

### H30 — Amazon 10-Q — Section heading

- Document: **0001018724-26-000014**, `amzn-20260331.htm`; `document:12e4f6041351020db0ab615654221fa03f4c919df5d4a48b732c40d34ad6f56c`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001018724-26-000014.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000014/amzn-20260331.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/e6/e6b80e48612abe3a0a8256e5ff3b5637cd4be94c12dc18cd3d7106667294fb8b), recovered source line 8; XPath `/*[1]/*[2]/*[56]/*[1]`.
- Block **43**, kind **heading**; full block ID `block:59a5703015b36a268634a6c6fbe9e2f26cbd5c0a70dae2b338b2eb9706a38c09`.
- Detected section **S2: classified; Part I, Item 1**; section ID `section:fa4beb67c9e5d18ed28352d88afe498446b91dad2a6ba5b5abb38679462e3c7e`; source heading “Item 1. Financial Statements”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[56]/*[1]`; normalized offsets `[2394, 2422)`; `text_sha256=1e935e401b5a5d833d81c30233ba41f988a1e06f047140ab9bffba1248819367`.
- Extracted text:

> Item 1. Financial Statements

Source element text for comparison (separate from extracted text):

> Item 1.Financial Statements

Why this matters: A short explicit item title starts this classified range; compare the original heading and the preceding content. This is an agent-inspected candidate for human adjudication.

Human disposition: **pending**.

### H31 — Amazon 10-Q — Table-of-contents candidate

- Document: **0001018724-26-000014**, `amzn-20260331.htm`; `document:12e4f6041351020db0ab615654221fa03f4c919df5d4a48b732c40d34ad6f56c`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001018724-26-000014.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000014/amzn-20260331.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/e6/e6b80e48612abe3a0a8256e5ff3b5637cd4be94c12dc18cd3d7106667294fb8b), recovered source line 8; XPath `/*[1]/*[2]/*[49]/*[1]`.
- Block **39**, kind **table**; full block ID `block:3717735665aac2fa7beb3b54bc83e04f0a985ec86e721f32ebefbf8ce3560a6c`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:2eee30e959d75359907c80978a7c86e422dbb5de6069ed745fd882bdb515b1b4`; source heading “Table of Contents”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[49]/*[1]`; normalized offsets `[2336, 2343)`; `text_sha256=1e935e401b5a5d833d81c30233ba41f988a1e06f047140ab9bffba1248819367`.
- Extracted text:

> [TABLE]

Source element text for comparison (separate from extracted text):

> PagePART I. FINANCIAL INFORMATIONItem 1.Financial Statements3Consolidated Statements of Cash Flows3Consolidated Statements of Operations4Consolidated Statements of Comprehensive Income5Consolidated Balance Sheets6Notes to Consolidated Financial Statements7Item 2.Management’s Discussion and Analysis of Financial Condition and Results of Operations25Item 3.Quantitative and Qualitative Disclosures About Market Risk34Item 4.Controls and Procedures35PART II. OTHER INFORMATIONItem 1.Legal Proceedings36Item 1A.Risk Factors36Item 2.Unregistered Sales of Equity Securities and Use of Proceeds48Item 3.Defaults Upon Senior Securities48Item 4.Mine Safety Disclosures48Item 5.Other Information48Item 6.Exhibits49Signatures50

Why this matters: Navigation must remain available without becoming a body item boundary. For an opaque table the extracted text is deliberately [TABLE]; the adjacent source excerpt exposes the candidate labels for review.

Human disposition: **pending**.

### H32 — Amazon 10-Q — Narrative near financial tables

- Document: **0001018724-26-000014**, `amzn-20260331.htm`; `document:12e4f6041351020db0ab615654221fa03f4c919df5d4a48b732c40d34ad6f56c`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001018724-26-000014.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000014/amzn-20260331.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/e6/e6b80e48612abe3a0a8256e5ff3b5637cd4be94c12dc18cd3d7106667294fb8b), recovered source line 8; XPath `/*[1]/*[2]/*[63]`.
- Block **49**, kind **paragraph**; full block ID `block:6e62da7b5f9c3021b5a9101809ad2ebf7bf68bb84c7807ccf5e4aa6ee1b15465`.
- Detected section **S2: classified; Part I, Item 1**; section ID `section:fa4beb67c9e5d18ed28352d88afe498446b91dad2a6ba5b5abb38679462e3c7e`; source heading “Item 1. Financial Statements”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[63]`; normalized offsets `[2512, 2572)`; `text_sha256=1e935e401b5a5d833d81c30233ba41f988a1e06f047140ab9bffba1248819367`.
- Extracted text:

> See accompanying notes to consolidated financial statements.

Adjacent opaque table: block **48**, `block:4c6527a474696bb3ef4e8406c45259a44f2722fb0d8041ca21a7ee825eab3743`, source XPath `/*[1]/*[2]/*[62]/*[1]`.

Why this matters: Checks narrative/table separation and section ownership around financial disclosure. Review the source table and nearby footnote or explanatory prose; no cell values or financial correctness are scored here.

Human disposition: **pending**.

### H33 — Alphabet 10-K — Section heading

- Document: **0001652044-25-000014**, `goog-20241231.htm`; `document:e049d1df6916c050fea8957e4e2d269743113f4186a6048db0152fba73f615a3`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001652044-25-000014.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1652044/000165204425000014/goog-20241231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/7b/7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d), recovered source line 8; XPath `/*[1]/*[2]/*[100]`.
- Block **88**, kind **heading**; full block ID `block:b699c9d9e32c7a4dc441e7cb9eb0a899f2d0eba073e767a4fa54b3bea6365126`.
- Detected section **S2: classified; Part I, Item 1**; section ID `section:b9bab4a5c30cd93ed5c993d22dbeb4f2bb41d5034a746f4ce3783223253fda37`; source heading “ITEM 1.BUSINESS”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[100]`; normalized offsets `[11522, 11537)`; `text_sha256=d563bb189415b9757d4c49915f8fe9d3021520bd5e03daec39df0ea3388ad098`.
- Extracted text:

> ITEM 1.BUSINESS

Why this matters: A short explicit item title starts this classified range; compare the original heading and the preceding content. This is an agent-inspected candidate for human adjudication.

Human disposition: **pending**.

### H34 — Alphabet 10-K — Table-of-contents candidate

- Document: **0001652044-25-000014**, `goog-20241231.htm`; `document:e049d1df6916c050fea8957e4e2d269743113f4186a6048db0152fba73f615a3`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001652044-25-000014.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1652044/000165204425000014/goog-20241231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/7b/7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d), recovered source line 8; XPath `/*[1]/*[2]/*[58]/*[2]`.
- Block **52**, kind **table**; full block ID `block:9007be2ef6ef4ee1f3ca0cc4eefda41500b7d1a98891fa6444c1626397daf86e`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:e2002bd51179162f0d8c3b8724ca1916a7f091149389a964678ac403c5554b3d`; source heading “[TABLE]”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[58]/*[2]`; normalized offsets `[5333, 5340)`; `text_sha256=d563bb189415b9757d4c49915f8fe9d3021520bd5e03daec39df0ea3388ad098`.
- Extracted text:

> [TABLE]

Source element text for comparison (separate from extracted text):

> PageNote About Forward-Looking Statements3PART IItem 1.Business4Item 1A.Risk Factors10Item 1B.Unresolved Staff Comments25Item 1C.Cybersecurity25Item 2.Properties26Item 3.Legal Proceedings26Item 4.Mine Safety Disclosures26PART IIItem 5.Market for Registrant’s Common Equity, Related Stockholder Matters, and Issuer Purchases of Equity Securities27Item 6.[Reserved]29Item 7.Management’s Discussion and Analysis of Financial Condition and Results of Operations30Item 7A.Quantitative and Qualitative Disclosures About Market Risk45Item 8.Financial Statements and Supplementary Data48Item 9.Changes in and Disagreements With Accountants on Accounting and Financial Disclosure90Item 9A.Controls and Procedures90Item 9B.Other I […]

Why this matters: Navigation must remain available without becoming a body item boundary. For an opaque table the extracted text is deliberately [TABLE]; the adjacent source excerpt exposes the candidate labels for review.

Human disposition: **pending**.

### H35 — Alphabet 10-K — Narrative near financial tables

- Document: **0001652044-25-000014**, `goog-20241231.htm`; `document:e049d1df6916c050fea8957e4e2d269743113f4186a6048db0152fba73f615a3`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001652044-25-000014.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1652044/000165204425000014/goog-20241231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/7b/7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d), recovered source line 8; XPath `/*[1]/*[2]/*[914]`.
- Block **805**, kind **paragraph**; full block ID `block:eecf0ef163471e72ae81e6046af87ce5a1952795082b6e5b5b09bfb3f3a3be1d`.
- Detected section **S14: classified; Part II, Item 8**; section ID `section:d7c3c97dc370591563cd0f4fe1d06ad0c4c8ed40a33d75c3b195f95880c1d02c`; source heading “ITEM 8.FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[914]`; normalized offsets `[203870, 204236)`; `text_sha256=d563bb189415b9757d4c49915f8fe9d3021520bd5e03daec39df0ea3388ad098`.
- Extracted text:

> Because of its inherent limitations, internal control over financial reporting may not prevent or detect misstatements. Also, projections of any evaluation of effectiveness to future periods are subject to the risk that controls may become inadequate because of changes in conditions, or that the degree of compliance with the policies or procedures may deteriorate.

Adjacent opaque table: block **806**, `block:239633647c7cf2888e79303d5eb0a424d36c8355ee74363dacd177ceb1e4db25`, source XPath `/*[1]/*[2]/*[915]/*[1]`.

Why this matters: Checks narrative/table separation and section ownership around financial disclosure. Review the source table and nearby footnote or explanatory prose; no cell values or financial correctness are scored here.

Human disposition: **pending**.

### H36 — Alphabet 10-K — Section transition

- Document: **0001652044-25-000014**, `goog-20241231.htm`; `document:e049d1df6916c050fea8957e4e2d269743113f4186a6048db0152fba73f615a3`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001652044-25-000014.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1652044/000165204425000014/goog-20241231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/7b/7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d), recovered source line 8; XPath `/*[1]/*[2]/*[227]`.
- Block **201**, kind **heading**; full block ID `block:90571f6b108e29d5d9840a23760f379dbb9b332ec1bd4c6a5c3fd7475139b238`.
- Detected section **S3: classified; Part I, Item 1A**; section ID `section:186fc29e89654279bde25d705ce8a80a7575354fbbe60e5b8fc3516cf1a9d8be`; source heading “ITEM 1A.RISK FACTORS”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[227]`; normalized offsets `[42031, 42051)`; `text_sha256=d563bb189415b9757d4c49915f8fe9d3021520bd5e03daec39df0ea3388ad098`.
- Extracted text:

> ITEM 1A.RISK FACTORS

Preceding block **200**, owned by **S2**: “We webcast via our investor relations YouTube channel and website our earnings calls and certain events we participate in or host with members of the investment community. Our investor relations websi […]”.

Why this matters: Tests the boundary from Business to Risk Factors. The immediately preceding block remains in the previous physical range; the new heading must start the next one.

Human disposition: **pending**.

### H37 — Alphabet 10-K — End of document

- Document: **0001652044-25-000014**, `goog-20241231.htm`; `document:e049d1df6916c050fea8957e4e2d269743113f4186a6048db0152fba73f615a3`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001652044-25-000014.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1652044/000165204425000014/goog-20241231.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/7b/7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d), recovered source line 8; XPath `/*[1]/*[2]/*[1262]/*[1]/*[1]`.
- Block **1379**, kind **paragraph**; full block ID `block:81919e86915f95e4111eb415a219e58c29db5e7594995c92d3333dd95994d225`.
- Detected section **S28: unclassified; Part unknown, Item none**; section ID `section:ed90b8320e7e15396736395c2ea49153c907731bb0733cb4a1e51f78efbde026`; source heading “SIGNATURES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[1262]/*[1]/*[1]`; normalized offsets `[301026, 301029)`; `text_sha256=d563bb189415b9757d4c49915f8fe9d3021520bd5e03daec39df0ea3388ad098`.
- Extracted text:

> 98.

Why this matters: Confirms that the final emitted block remains source-linked and owned. An annual filing may place substantial annex or report content after signatures; this is physical ownership rather than resolved incorporation by reference.

Human disposition: **pending**.

### H38 — Alphabet 10-Q — Section heading

- Document: **0001652044-26-000048**, `goog-20260331.htm`; `document:7e4c54f8a342fe573df488ab14a804a0cb3ae65923a0ff4eca7ee0cb3a546719`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001652044-26-000048.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000048/goog-20260331.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/0d/0da733204ca3463c96d324c3620ab2794bce9566ee7a6586100b66634a98aca0), recovered source line 8; XPath `/*[1]/*[2]/*[58]`.
- Block **50**, kind **heading**; full block ID `block:b77b92d1495437214b72e7cd0b291b2ff9f772bbc1cccc9475e23d24a243eb8a`.
- Detected section **S2: classified; Part I, Item 1**; section ID `section:ba2e4dbe3a202b4732032d62647e0a50e69aa167ccc084194cba46027e9a5526`; source heading “ITEM 1.FINANCIAL STATEMENTS”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[58]`; normalized offsets `[5972, 5999)`; `text_sha256=be0dcde6244a2daacb0a0d0527b0222fe9ad825118b06ae951ac952fc8d53f92`.
- Extracted text:

> ITEM 1.FINANCIAL STATEMENTS

Why this matters: A short explicit item title starts this classified range; compare the original heading and the preceding content. This is an agent-inspected candidate for human adjudication.

Human disposition: **pending**.

### H39 — Alphabet 10-Q — Table-of-contents candidate

- Document: **0001652044-26-000048**, `goog-20260331.htm`; `document:7e4c54f8a342fe573df488ab14a804a0cb3ae65923a0ff4eca7ee0cb3a546719`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001652044-26-000048.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000048/goog-20260331.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/0d/0da733204ca3463c96d324c3620ab2794bce9566ee7a6586100b66634a98aca0), recovered source line 8; XPath `/*[1]/*[2]/*[42]/*[2]`.
- Block **40**, kind **table**; full block ID `block:b8a477b1d8f8d70eefde70ac22534a19a21e775ef34bbd500af4e61f9a29f69c`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:9b4cbb259c51558f759bb965e43e1eb0d08f47723ca6e5dc21b835547062c3eb`; source heading “[TABLE]”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[42]/*[2]`; normalized offsets `[2695, 2702)`; `text_sha256=be0dcde6244a2daacb0a0d0527b0222fe9ad825118b06ae951ac952fc8d53f92`.
- Extracted text:

> [TABLE]

Source element text for comparison (separate from extracted text):

> Page No.Note About Forward-Looking Statements3PART I. FINANCIAL INFORMATIONItem 1Financial Statements4Consolidated Balance Sheets - December 31, 2025 and March 31, 20264Consolidated Statements of Income - Three Months Ended March 31, 2025 and 20265Consolidated Statements of Comprehensive Income - Three Months Ended March 31, 2025 and 20266Consolidated Statements of Stockholders' Equity - Three Months Ended March 31, 2025 and 20267Consolidated Statements of Cash Flows - Three Months Ended March 31, 2025 and 20268Notes to Consolidated Financial Statements9Item 2Management’s Discussion and Analysis of Financial Condition and Results of Operations35Item 3Quantitative and Qualitative Disclosures About Market Risk48I […]

Why this matters: Navigation must remain available without becoming a body item boundary. For an opaque table the extracted text is deliberately [TABLE]; the adjacent source excerpt exposes the candidate labels for review.

Human disposition: **pending**.

### H40 — Alphabet 10-Q — Narrative near financial tables

- Document: **0001652044-26-000048**, `goog-20260331.htm`; `document:7e4c54f8a342fe573df488ab14a804a0cb3ae65923a0ff4eca7ee0cb3a546719`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001652044-26-000048.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000048/goog-20260331.htm#f-365); [exact local bytes](../.runtime/artifacts/bronze/sha256/0d/0da733204ca3463c96d324c3620ab2794bce9566ee7a6586100b66634a98aca0), recovered source line 8; XPath `/*[1]/*[2]/*[119]/*[2]/*[1]`.
- Block **114**, kind **paragraph**; full block ID `block:bd2ffa5998484c51aaed4dabc4049280eaff5058e758ad35283214b1206d404a`.
- Detected section **S2: classified; Part I, Item 1**; section ID `section:ba2e4dbe3a202b4732032d62647e0a50e69aa167ccc084194cba46027e9a5526`; source heading “ITEM 1.FINANCIAL STATEMENTS”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[119]/*[2]/*[1]`; normalized offsets `[12306, 12380)`; `text_sha256=be0dcde6244a2daacb0a0d0527b0222fe9ad825118b06ae951ac952fc8d53f92`.
- Extracted text:

> The following table presents revenues disaggregated by type (in millions):

Source element text for comparison (separate from extracted text):

> The following table presents revenues disaggregated by type (in millions): Three Months EndedMarch 31,20252026Google Search & other$50,702 $60,399 YouTube ads8,927 9,883 Google Network7,256 6,971 Google advertising66,885 77,253 Google subscriptions, platforms, and devices10,379 12,384 Google Services total77,264 89,637 Google Cloud12,260 20,028 Other Bets450 411 Hedging gains (losses)260 (180)Total revenues$90,234 $109,896

Adjacent opaque table: block **115**, `block:e54b8b43bc2c80d3558f71510275e325c7a24bc74accd66b0ce5582c487c16a9`, source XPath `/*[1]/*[2]/*[119]/*[2]/*[1]/*[2]`.

Why this matters: Checks narrative/table separation and section ownership around financial disclosure. Review the source table and nearby footnote or explanatory prose; no cell values or financial correctness are scored here.

Human disposition: **pending**.

### H41 — JPMorgan Chase & Co. 10-Q — JPMorgan introduction heading in table

- Document: **0001628280-26-029344**, `jpm-20260331.htm`; `document:3150c4203a3994c1a0a4b2d65550a0a25942c608f619840f0234683a77756351`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-029344.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026029344/jpm-20260331.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/19/19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc), recovered source line 8; XPath `/*[1]/*[2]/*[51]/*[1]`.
- Block **36**, kind **table**; full block ID `block:a911a00086bebd4bdb757ce68c08477f77b321937b3a71609a62f083d0ebf803`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:6debeda1ccc014e10ebf1fe1f121df47058e76cd854f8dc7e6603d5a8eb213d8`; source heading “UNITED STATES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[51]/*[1]`; normalized offsets `[2965, 2972)`; `text_sha256=1af0d153598ad2f111296aedd6e822b0c13cd821bb761246fade60a9e35bcad5`.
- Extracted text:

> [TABLE]

Source element text for comparison (separate from extracted text):

> INTRODUCTION

Why this matters: The INTRODUCTION display heading is inside an opaque layout table immediately before MD&A. It survives in the HTML/table locator, but is not an explicit Item 2 heading.

Human disposition: **pending**.

### H42 — JPMorgan Chase & Co. 10-Q — JPMorgan MD&A narrative

- Document: **0001628280-26-029344**, `jpm-20260331.htm`; `document:3150c4203a3994c1a0a4b2d65550a0a25942c608f619840f0234683a77756351`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-029344.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026029344/jpm-20260331.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/19/19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc), recovered source line 8; XPath `/*[1]/*[2]/*[53]/*[1]/*[1]`.
- Block **37**, kind **paragraph**; full block ID `block:0fd5348a45fc63ca736acda78fbb4726daf6489bafdc4ee8afe26db0faf0f877`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:6debeda1ccc014e10ebf1fe1f121df47058e76cd854f8dc7e6603d5a8eb213d8`; source heading “UNITED STATES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[53]/*[1]/*[1]`; normalized offsets `[2973, 3175)`; `text_sha256=1af0d153598ad2f111296aedd6e822b0c13cd821bb761246fade60a9e35bcad5`.
- Extracted text:

> The following is Management’s discussion and analysis of the financial condition and results of operations (“MD&A”) of JPMorgan Chase & Co. (“JPMorganChase” or the “Firm”) for the first quarter of 2026.

Why this matters: MD&A prose survives before the financial statements, in the initial unclassified range; it is not assigned to Part II Item 2.

Human disposition: **pending**.

### H43 — JPMorgan Chase & Co. 10-Q — JPMorgan financial statement heading

- Document: **0001628280-26-029344**, `jpm-20260331.htm`; `document:3150c4203a3994c1a0a4b2d65550a0a25942c608f619840f0234683a77756351`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-029344.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026029344/jpm-20260331.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/19/19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc), recovered source line 8; XPath `/*[1]/*[2]/*[607]`.
- Block **1023**, kind **paragraph**; full block ID `block:6f427993e0023f4177a5758a725c1370fae48f8540cdd790cc80ccd0c29a45da`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:6debeda1ccc014e10ebf1fe1f121df47058e76cd854f8dc7e6603d5a8eb213d8`; source heading “UNITED STATES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[607]`; normalized offsets `[173432, 173477)`; `text_sha256=1af0d153598ad2f111296aedd6e822b0c13cd821bb761246fade60a9e35bcad5`.
- Extracted text:

> Consolidated statements of income (unaudited)

Why this matters: Financial statement title survives as a paragraph, without an explicit body Item 1 prefix or active Part I context.

Human disposition: **pending**.

### H44 — JPMorgan Chase & Co. 10-Q — JPMorgan missing-part boundary

- Document: **0001628280-26-029344**, `jpm-20260331.htm`; `document:3150c4203a3994c1a0a4b2d65550a0a25942c608f619840f0234683a77756351`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-029344.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026029344/jpm-20260331.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/19/19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc), recovered source line 8; XPath `/*[1]/*[2]/*[1135]/*[1]/*[1]`.
- Block **2234**, kind **paragraph**; full block ID `block:a54296a2c8f09cb4dd494691ad7d337bd48195e5cda30cf708bfb0a8958a44c7`.
- Detected section **S1: ambiguous; Part unknown, Item 3**; section ID `section:063e97e6d9965c85a2afbd5bd0a359350216627d1c6467b75230b8399b2af4c9`; source heading “Item 3. Quantitative and Qualitative Disclosures About Market Risk.”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[1135]/*[1]/*[1]`; normalized offsets `[377410, 377477)`; `text_sha256=1af0d153598ad2f111296aedd6e822b0c13cd821bb761246fade60a9e35bcad5`.
- Extracted text:

> Item 3. Quantitative and Qualitative Disclosures About Market Risk.

Why this matters: The explicit Item 3 title is retained, but the part remains unknown. Check that the preceding unclassified range ends immediately before it.

Human disposition: **pending**.

### H45 — JPMorgan Chase & Co. 10-Q — JPMorgan Part II transition

- Document: **0001628280-26-029344**, `jpm-20260331.htm`; `document:3150c4203a3994c1a0a4b2d65550a0a25942c608f619840f0234683a77756351`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-029344.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026029344/jpm-20260331.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/19/19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc), recovered source line 8; XPath `/*[1]/*[2]/*[1135]/*[1]/*[8]`.
- Block **2239**, kind **heading**; full block ID `block:4a8336220f4644614813e4124b3df606e230ea1fe3dd2fa00b6d706047148c5c`.
- Detected section **S3: unclassified; Part II, Item none**; section ID `section:b31f6d5900a51d046fade205de2f3a20da48fd96e979eb1c3e7e34b095144811`; source heading “Part II – Other Information”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[1135]/*[1]/*[8]`; normalized offsets `[379424, 379451)`; `text_sha256=1af0d153598ad2f111296aedd6e822b0c13cd821bb761246fade60a9e35bcad5`.
- Extracted text:

> Part II – Other Information

Why this matters: Explicit Part II begins a new preamble, preventing the prior financial/MD&A material from being absorbed into Part II items.

Human disposition: **pending**.

### H46 — JPMorgan Chase & Co. 10-Q — JPMorgan introduction heading in table

- Document: **0001628280-26-054343**, `jpm-20260630.htm`; `document:c768c0527dfc3d9b11170ed9d378db4aacd6da9c3b62710e6f78ca13432fc8c1`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-054343.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026054343/jpm-20260630.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/7c/7cbc765c34c9a43a09b74db21e75bd0f94e548b4dfb50c53699526a985935a48), recovered source line 8; XPath `/*[1]/*[2]/*[53]/*[1]`.
- Block **38**, kind **table**; full block ID `block:fb9feb4e1b7bf0bb9dc41bc925f2ad2732c695262549945a1499686a5983d2bb`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:fd39c31cbd891020ea62247623407ab10f2778b3c5b5416af14c9fc17553bb37`; source heading “UNITED STATES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[53]/*[1]`; normalized offsets `[3490, 3497)`; `text_sha256=da3294fe1a28ca054cf1aa7e898c35e0c5871bb4efb6d733631b6519ed530dcb`.
- Extracted text:

> [TABLE]

Source element text for comparison (separate from extracted text):

> INTRODUCTION

Why this matters: The INTRODUCTION display heading is inside an opaque layout table immediately before MD&A. It survives in the HTML/table locator, but is not an explicit Item 2 heading.

Human disposition: **pending**.

### H47 — JPMorgan Chase & Co. 10-Q — JPMorgan MD&A narrative

- Document: **0001628280-26-054343**, `jpm-20260630.htm`; `document:c768c0527dfc3d9b11170ed9d378db4aacd6da9c3b62710e6f78ca13432fc8c1`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-054343.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026054343/jpm-20260630.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/7c/7cbc765c34c9a43a09b74db21e75bd0f94e548b4dfb50c53699526a985935a48), recovered source line 8; XPath `/*[1]/*[2]/*[55]/*[1]/*[1]`.
- Block **39**, kind **paragraph**; full block ID `block:4373789cc3a7ea00bca2a29c1da8637b484c83429d2ca13f39d26b149afb7a93`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:fd39c31cbd891020ea62247623407ab10f2778b3c5b5416af14c9fc17553bb37`; source heading “UNITED STATES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[55]/*[1]/*[1]`; normalized offsets `[3498, 3701)`; `text_sha256=da3294fe1a28ca054cf1aa7e898c35e0c5871bb4efb6d733631b6519ed530dcb`.
- Extracted text:

> The following is Management’s discussion and analysis of the financial condition and results of operations (“MD&A”) of JPMorgan Chase & Co. (“JPMorganChase” or the “Firm”) for the second quarter of 2026.

Why this matters: MD&A prose survives before the financial statements, in the initial unclassified range; it is not assigned to Part II Item 2.

Human disposition: **pending**.

### H48 — JPMorgan Chase & Co. 10-Q — JPMorgan financial statement heading

- Document: **0001628280-26-054343**, `jpm-20260630.htm`; `document:c768c0527dfc3d9b11170ed9d378db4aacd6da9c3b62710e6f78ca13432fc8c1`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-054343.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026054343/jpm-20260630.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/7c/7cbc765c34c9a43a09b74db21e75bd0f94e548b4dfb50c53699526a985935a48), recovered source line 8; XPath `/*[1]/*[2]/*[743]`.
- Block **1148**, kind **paragraph**; full block ID `block:41e2ec016252d4332128225eb3ac515cbac77c538573499c6717a71fe31e948b`.
- Detected section **S0: unclassified; Part unknown, Item none**; section ID `section:fd39c31cbd891020ea62247623407ab10f2778b3c5b5416af14c9fc17553bb37`; source heading “UNITED STATES”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[743]`; normalized offsets `[192874, 192919)`; `text_sha256=da3294fe1a28ca054cf1aa7e898c35e0c5871bb4efb6d733631b6519ed530dcb`.
- Extracted text:

> Consolidated statements of income (unaudited)

Why this matters: Financial statement title survives as a paragraph, without an explicit body Item 1 prefix or active Part I context.

Human disposition: **pending**.

### H49 — JPMorgan Chase & Co. 10-Q — JPMorgan missing-part boundary

- Document: **0001628280-26-054343**, `jpm-20260630.htm`; `document:c768c0527dfc3d9b11170ed9d378db4aacd6da9c3b62710e6f78ca13432fc8c1`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-054343.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026054343/jpm-20260630.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/7c/7cbc765c34c9a43a09b74db21e75bd0f94e548b4dfb50c53699526a985935a48), recovered source line 8; XPath `/*[1]/*[2]/*[1328]/*[1]/*[1]`.
- Block **2402**, kind **paragraph**; full block ID `block:9e23743017e6d295c171128c185d1ef5f062da950d74fb60049cc1a636feb3bd`.
- Detected section **S1: ambiguous; Part unknown, Item 3**; section ID `section:45f7d2fe0e7f6f6b426d773a7baef3801e2300d11f36cdc316e58719d2a49e13`; source heading “Item 3. Quantitative and Qualitative Disclosures About Market Risk.”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[1328]/*[1]/*[1]`; normalized offsets `[402324, 402391)`; `text_sha256=da3294fe1a28ca054cf1aa7e898c35e0c5871bb4efb6d733631b6519ed530dcb`.
- Extracted text:

> Item 3. Quantitative and Qualitative Disclosures About Market Risk.

Why this matters: The explicit Item 3 title is retained, but the part remains unknown. Check that the preceding unclassified range ends immediately before it.

Human disposition: **pending**.

### H50 — JPMorgan Chase & Co. 10-Q — JPMorgan Part II transition

- Document: **0001628280-26-054343**, `jpm-20260630.htm`; `document:c768c0527dfc3d9b11170ed9d378db4aacd6da9c3b62710e6f78ca13432fc8c1`; [full parsed document](../.runtime/wp32-acceptance/replay-documents/0001628280-26-054343.json).
- Source HTML: [SEC original / nearby source anchor](https://www.sec.gov/Archives/edgar/data/19617/000162828026054343/jpm-20260630.htm); [exact local bytes](../.runtime/artifacts/bronze/sha256/7c/7cbc765c34c9a43a09b74db21e75bd0f94e548b4dfb50c53699526a985935a48), recovered source line 8; XPath `/*[1]/*[2]/*[1328]/*[1]/*[8]`.
- Block **2407**, kind **heading**; full block ID `block:c998073908a3680333df8992b4625c1363c7f323ae27e98c9b38d7ed5bd87f1a`.
- Detected section **S3: unclassified; Part II, Item none**; section ID `section:4a4acc25548657ab78a13d6bf6f4165106abc980f7853bb1feb75a028e918712`; source heading “Part II – Other Information”.
- Source locator: `kind=dom`; `path=/*[1]/*[2]/*[1328]/*[1]/*[8]`; normalized offsets `[404337, 404364)`; `text_sha256=da3294fe1a28ca054cf1aa7e898c35e0c5871bb4efb6d733631b6519ed530dcb`.
- Extracted text:

> Part II – Other Information

Why this matters: Explicit Part II begins a new preamble, preventing the prior financial/MD&A material from being absorbed into Part II items.

Human disposition: **pending**.

## Acceptance criteria and package stop

- **Satisfied:** rerun all-18 parsing/provenance/replay; 22,453 unique locator resolutions and offset checks; 25 frozen selected boundaries; unchanged seven held-out checks; complete per-filing register and all 364 range start/end IDs; at least 30 review samples with original references; both JPMorgan investigations; full automated quality gate; successful distribution validation; risks and readiness recommendation.
- **Outstanding:** independent human sample/boundary adjudication; broader section-quality labels and semantic coverage; documented JPMorgan retrieval limitations; future financial-table correctness and retrieval evaluation. No acceptance metric is replaced with an invented corpus-wide accuracy claim.
- **Architecture/deviations:** follows ADR-003 and architecture 3.1; no schema, parser, dependency or architecture change. Review-only temporary scripts/outputs remain ignored under `.runtime`; distribution checks create ignored `dist` artifacts. The only tracked addition is `docs/phase-3-wp3.2-acceptance-review.md`. No commit, push, branch switch or publication occurred.
- **Next recommended package:** separately authorize WP3.3 structured table extraction using preserved table locators, including unclassified/ambiguous sections, with source-reviewed table fixtures and explicit unknown metadata. Stop here; do not implement WP3.3 automatically.

Final verification: **PASS** — the document validator confirmed 18 filing entries, all 364 section ranges and their exact start/end IDs, 50 distinct samples across 11 filings, all 137 local evidence links, valid UTF-8, table structure, balanced fences, clean whitespace and unchanged parser/lock freeze hashes. `git diff --check` passed. Final `git status --short` showed only this new review document; implementation, tests, configuration, dependencies and existing documentation are unchanged. The samples remain pending human adjudication.
