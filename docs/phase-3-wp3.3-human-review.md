# WP3.3 human review log

## Candidate 1: JPMorgan consolidated statements of income

Status: **partial review; table acceptance pending**.
Review date: 2026-10-21, Asia/Kuala_Lumpur.
Reviewer: repository user, readings supplied in chat. Codex compared the readings
with the existing extraction; this is assisted review, not a blind benchmark.

- Accession: `0001628280-26-008131`.
- Source SHA-256: `428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05`.
- Table ID: `table:b88999f114400d9cbcdcc23ca1e38b7fb3cb752be7ab0bba62139c891c767bea`.
- Source DOM: `/*[1]/*[2]/*[1111]/*[1]`; printed page 165.
- [Original filing](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm).
- [Extracted document](../.runtime/wp33/completion-documents/0001628280-26-008131.json).

Seven supplied readings match the extracted text and the five selected amount
records' row/year associations:

1. Years, left to right: **2025, 2024, 2023**. Extracted header cells are on
   zero-based row 1, starting at columns 3, 9, and 15.
2. Units heading: **(in millions, except per share data)**. The wording is retained
   in the raw heading and table unit hints. Per-cell currency, unit, and scale
   remain null; preserving the heading does not establish resolved financial context.
3. 2025 total net revenue: displayed **182,447**, parsed Decimal **182447**;
   zero-based row 16, column 3. Headers link to `2025` and `Total net revenue`.
4. 2025 diluted earnings per share: displayed **20.02**, parsed Decimal **20.02**;
   zero-based row 34, column 3. Headers link to `2025` and
   `Diluted earnings per share`. The displayed value has not been multiplied by
   a million.
5. 2025 investment securities losses: the user read **(57)** and identified it
   as negative. The extraction preserves `(57)`, parses Decimal **-57**, and
   records `sign=negative`, `missing=false`; zero-based row 8, column 3.
   Headers link to `2025` and `Investment securities losses`.
6. 2024 total net revenue: the user read **177,556**. Extracted Decimal
   **177556**, zero-based row 16, column 9; headers link to `2024` and
   `Total net revenue`.
7. 2023 total net revenue: the user read **158,104**. Extracted Decimal
   **158104**, zero-based row 16, column 15; headers link to `2023` and
   `Total net revenue`.

No disagreement was found in these seven checks. This does not certify all cells,
the table category, complete measurement intervals, currency or mixed-unit
application. Footnotes and other
relevant cases remain to be reviewed. Neither the candidate nor the corpus is
marked fully adjudicated. Codex explained that the millions scale excludes
per-share data. The user was unsure and subsequently proposed applying that
multiplier to EPS; Codex corrected the interpretation. It is not recorded as an
independently confirmed unit check. Structured unit/scale resolution remains
unimplemented. At the user's request, review moved to candidate 2.

## Candidate 2: JPMorgan consolidated balance sheets analysis

Status: **partial review; table acceptance pending**.

- Accession: `0001628280-26-008131`; same source SHA-256 as candidate 1.
- Table ID: `table:27706204014dc90a3800787850b9873358000aae8c8c95ddfa7390bb6d61bdc2`.
- Source DOM: `/*[1]/*[2]/*[356]/*[1]`; printed page 55.
- [Original filing](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm).
- [Extracted document](../.runtime/wp33/completion-documents/0001628280-26-008131.json).

The user supplied the following readings, which match the extraction:

1. Headings: **2025, 2024, Change**. These are retained as header cells on
   zero-based row 2, starting at columns 3, 9, and 12. Codex supplied the heading
   wording before the user repeated it; this is an assisted confirmation, not an
   independently elicited heading label.
2. 2025 total assets: displayed **4,424,900**, parsed Decimal **4424900**;
   zero-based row 19, column 4. Headers link to `2025` and `Total assets`.
3. 2024 total assets: displayed **4,002,814**, parsed Decimal **4002814**;
   zero-based row 19, column 10. Headers link to `2024` and `Total assets`.

No disagreement was found in these selected readings and amount associations.
No whole-table acceptance or resolved financial context is recorded. Further
review should distinguish selected balance-sheet analysis from a full statement
and address the separately displayed percentage symbols in the change column.

### WP33-REV-001: separate percentage symbol is not associated with its amount

Status: **confirmed financial-context limitation; unresolved**.

The user read **11 %** in the `Total assets` / `Change` entry. Both source
tokens are preserved, and both link to `Change` and `Total assets`, but the
extraction represents them independently:

- Row 19, column 12, spanning two columns: raw `11` plus trailing nonbreaking
  whitespace, Decimal `11`, normalization `percentage=false`.
- Row 19, column 14: raw `%`, normalization `not_numeric`, no value.

Consequently, the result does not represent the combined entry as 11 percent.
Lexical parsing is consistent with its single-cell policy, but financial consumers
cannot treat the number's percentage flag as the resolved meaning of the entry.
This is a concrete instance of the documented separate-symbol context limitation,
not a lost source cell or a failed year association.

Required remediation before claiming this entry's financial interpretation is
correct: associate the percent symbol through a bounded, source-linked context
policy, or explicitly abstain/flag the amount's unresolved unit. Preserve the raw
cells and provenance, add regression coverage for the selected policy, and replay
affected outputs. No implementation change or table acceptance is recorded here.

### WP33-REV-002: selected analysis data classified as a full statement

Status: **source extent confirmed by user; classification correction recommended,
unresolved**.

The user read **Selected Consolidated balance sheets data** above the year
headings. The extraction preserves this exact text at zero-based row 1, column 0,
spanning 12 columns. This was an assisted caption check: Codex supplied the
starting word before the user supplied the complete wording.

The extractor assigns `financial_statement` using
`statement_title_and_numeric_cells` and the nearby title
`Consolidated balance sheets analysis`. Codex's inspection of the extracted rows
shows asset entries ending at `Total assets`, with no liability or equity rows in
this table. Together with the selected-data wording and surrounding analysis,
this supports a proposed `financial_disclosure` classification rather than a
full balance-sheet statement. The category judgment is Codex's assessment, not a
user-confirmed financial label. No classifier change has been made.

The user subsequently supplied a screenshot showing the table ending at
`Total assets`, followed by explanatory text, and explicitly confirmed that this
particular table ends there. The selected-data caption and source extent are now
human-confirmed. The proposed `financial_disclosure` category remains Codex's
assessment based on those observations, rather than an independent human category
label. No classifier repair or whole-table financial acceptance is recorded.

Candidate 2 has two recorded findings requiring remediation or an explicitly
reviewed scope disposition: WP33-REV-001 (percentage context) and WP33-REV-002
(selected analysis classified as a statement). Its reviewed total-assets amounts
and their year associations match; that does not close either finding.

## Candidate 3: JPMorgan consolidated statements of cash flows

Status: **partial review; table acceptance pending**.

- Accession: `0001628280-26-008131`; same source SHA-256 as candidate 1.
- Table ID: `table:f093360b59fdfa9198c3827cfe3d9b601cc27eaded5f95011cde8d78eac985f3`.
- Source DOM: `/*[1]/*[2]/*[1138]/*[1]`; printed page 169.
- [Original filing](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm).
- [Extracted document](../.runtime/wp33/completion-documents/0001628280-26-008131.json).

The user supplied two matching 2025 source readings:

1. Net income: **$57,048**. The amount cell retains `57,048` plus trailing
   nonbreaking whitespace and parses Decimal **57048** at zero-based row 3,
   column 4, linked to `2025` and `Net income`. The dollar symbol remains a
   separate source cell; structured currency is unknown. The supplied screenshot
   also shows this amount under 2025.
2. Net cash (used in)/provided by operating activities: **(147,782)**.
   The extraction preserves the parentheses, parses Decimal **-147782**, and
   records a negative sign at zero-based row 21, column 3. Headers link to
   `2025` and the correct operating cash-flow subtotal. This reading was supplied
   in the user's text; the attached screenshot shows only the upper table portion.

No disagreement was found in these two amount readings and associations. No
whole-table acceptance or resolved currency/scale is recorded. Candidate 2's
findings remain open. The next source-reading check is the symbol displayed for
2025 `Initial gain on the Visa share exchange`, to inspect dash handling without
assuming its financial meaning.

### WP33-REV-003: leading em dash classified as a row header

Status: **structural defect; source tokens confirmed by user; unresolved**.

The user read the row as **—, (7,990), —** for 2025, 2024, 2023, matching the
extracted raw tokens. Codex had already shown these values in chat, so this is
an assisted confirmation. The user chose to continue review before remediation.

Before the user's reading, Codex inspected row 9 (`Initial gain on the Visa share
exchange`). The 2025 cell (column 3) is raw `—` (U+2014) plus nonbreaking space;
2024 is `(7,990)`; 2023 is `—`. Row 8 (`Estimated bargain purchase gain…`) has the
same pattern.

`header_roles` (`processing/tables.py`) treats non-amount cells left of a row's
first numeric cell as row headers. Its exclusion set contains `-` and U+2212 but
not U+2014/U+2013. Consequently:

- The 2025 dash is `is_header=true` and has no link to `2025` or its row label.
- The 2024 `-7990` and 2023 dash link to the 2025 dash as an extra row header.

Corpus scan of the current completion documents: **800** en/em-dash cells marked
as headers in **135 tables** across **17 of 18 filings**; **6,232** cells carry a
spurious dash header link. JPMorgan accounts for 514 of those dash headers.
Amounts and year links are not lost, but header context is wrong and dash cells
are detached from their period. Existing tests did not cover a leading em dash.

Proposed remediation (not implemented; user chose to continue review first): treat dash/placeholder tokens as
non-headers in `header_roles`, add a regression for a leading-em-dash row, bump
the extractor version, and replay the corpus. Whether the dash means zero or
missing remains a separate, unresolved semantic question.

## Candidate 4: JPMorgan Q1 2026 consolidated balance sheets analysis

Status: **partial review; table acceptance pending**.

- Accession: `0001628280-26-029344` (10-Q).
- Source SHA-256: `19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc`.
- Table ID: `table:f657af3e070e0c01d72515087c36787e6be317ad9fa8e1bb93306e95688bd98a`.
- Source DOM: `/*[1]/*[2]/*[95]/*[1]`; printed page 12.
- [Original filing](https://www.sec.gov/Archives/edgar/data/19617/000162828026029344/jpm-20260331.htm).
- [Extracted document](../.runtime/wp33/completion-documents/0001628280-26-029344.json).

Codex withheld extracted values before asking; the user's readings match:

1. Date headings: **March 31, 2026; December 31, 2025**. Header cells on
   zero-based row 2, columns 3 and 9 (status `uncertain`; dates are not
   parsed as periods).
2. March 31, 2026 total assets: **$ 4,900,475**. Decimal **4900475** at row 19,
   column 4, linked to `March 31, 2026` and `Total assets`; `$` is a separate
   cell. The December 31, 2025 column's **4424900** equals candidate 2's
   10-K 2025 total assets, a consistent cross-filing reading.
3. Deposits with banks change: **(10)**. Decimal **-10**, row 5, column 12,
   linked to `Change` and the row label; `percentage=false` (see below).
4. Goodwill, MSRs and other intangible assets change: **—**. Retained raw U+2014,
   status `uncertain`, linked to `Change` and the row label. It is not a leading
   dash, so WP33-REV-003 does not apply. Its meaning (zero, rounded below 1%,
   or not meaningful) is not established.
5. `%` appears **only on the first and last rows** (`Cash and due from banks`,
   `Total assets`).

Codex also verified that the 34-row shape is faithful: source rows 20–33 are
blank spacer rows, retained as empty cells. The caption `Selected Consolidated
balance sheets data` and asset-only extent repeat candidate 2's pattern, so
WP33-REV-002 applies here as well (`financial_statement` predicted).

**WP33-REV-001 extended:** the user's reading shows the percent unit is a column
convention, displayed only on the first and total rows. The 13 intermediate
`Change` amounts carry no adjacent `%` cell, so associating adjacent symbols alone
would leave them unitless. A remedy must either apply a bounded, source-linked
column-level unit policy or flag every `Change` amount's unit as unresolved.

## Candidate 5: JPMorgan Q2 2026 consolidated balance sheets analysis

Status: **partial review; table acceptance pending**.

- Accession: `0001628280-26-054343` (10-Q).
- Source SHA-256: `7cbc765c34c9a43a09b74db21e75bd0f94e548b4dfb50c53699526a985935a48`.
- Table ID: `table:e277c418d611747116a2599a59086c0c7aaa9604f801be87e1a6e04299eb5e00`.
- Source DOM: `/*[1]/*[2]/*[123]/*[1]`; printed page 15.
- [Original filing](https://www.sec.gov/Archives/edgar/data/19617/000162828026054343/jpm-20260630.htm).
- [Extracted document](../.runtime/wp33/completion-documents/0001628280-26-054343.json).

Codex withheld extracted values before asking; the user's readings match:

1. Date headings: **June 30, 2026; December 31, 2025** (row 2, columns 3 and 9).
2. June 30, 2026 total assets: **$ 5,015,069**. Decimal **5015069**, row 19,
   column 4, linked to `June 30, 2026` and `Total assets`. December 31, 2025
   again extracts **4424900**, consistent with candidates 2 and 4.
3. Allowance for loan losses: **(26,152)**, **(25,765)**, change **2**. Decimals
   **-26152**, **-25765**, **2** (row 13, columns 3, 9, 12), each linked to its
   period/`Change` and the row label.
4. Held-to-maturity securities change: **(1)**. Decimal **-1**, row 10, column 12.
5. `%` appears only on the first and last rows; `Goodwill, MSRs and other
   intangible assets` shows **—** (raw U+2014, `uncertain`, correctly linked).

The user also observed that `$` appears only on the first and last rows. The
extraction keeps those `$` as separate `not_numeric` cells; structured currency
remains null for every amount. This is the same column-convention pattern as
the percent unit in WP33-REV-001 and must be addressed by any future currency
policy; it is already a documented limitation, not a new defect.

Codex reasonableness check (Decimal, not a pipeline feature): recomputed changes
from the extracted amounts are 13.34% (total assets), 1.50% (allowance) and
-0.61% (held-to-maturity), consistent with the displayed rounded 13, 2 and (1).
For the allowance, signed division of two negative amounts gives the positive
change, so the accounting-negative parse is consistent with the source.
WP33-REV-001 and WP33-REV-002 recur unchanged; WP33-REV-003 does not occur in
this table.

## Candidate 6: Apple Q2 FY2026 condensed consolidated statements of operations

Status: **partial review; table acceptance pending**.

- Accession: `0000320193-26-000013` (10-Q).
- Source SHA-256: `7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91`.
- Table ID: `table:97d9b6d67fd25824c9695d12a27e66092cb058f304428b9014b0de0847283466`.
- Source DOM: `/*[1]/*[2]/*[64]/*[1]`; printed page 1.
- [Original filing](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm).
- [Extracted document](../.runtime/wp33/completion-documents/0000320193-26-000013.json).

Codex withheld extracted values before asking; the user's readings match:

1. Group headings **Three Months Ended** and **Six Months Ended**, each over
   **March 28, 2026; March 29, 2025**. Extracted: groups on row 1 (columns 3 and
   15, each spanning 9); dates on row 2 (columns 3, 9, 15, 21). Every amount links
   to its duration group and its date, so the duplicated date text is
   disambiguated by the group header.
2. Cost of sales / Products, three months ended March 28, 2026: **49,179**.
   Decimal **49179**, row 9, column 3.
3. Other income/(expense), net: **(52), (279), 98, (527)**. Decimals
   **-52, -279, 98, -527** (row 20), each with the correct group/date links; the
   positive six-month value amid negatives is preserved.
4. Shares used / Basic, six months ended March 28, 2026: **14,710,718**.
   Decimal **14710718**, row 30, column 15.
5. Diluted EPS, three months ended March 28, 2026: **$ 2.01**. Decimal **2.01**,
   row 27, column 4; `$` is a separate cell.

6. Units line, after Codex clarified its location (screenshot supplied):
   **(In millions, except number of shares, which are reflected in thousands, and
   per-share amounts)**. See WP33-REV-005.

### WP33-REV-004: row-group labels are not linked; duplicate row labels are ambiguous

Status: **structural defect confirmed by user reading; unresolved**.

Rows such as `Net sales:`, `Cost of sales:`, `Earnings per share:` and `Shares
used in computing earnings per share:` contain no amounts, so `header_roles`
does not mark them as headers and no amount links to them. The leaf labels
`Products`, `Services`, `Basic` and `Diluted` each occur twice. Consequently
the user-confirmed cost-of-sales Products amount 49179 has the same header text
(`Three Months Ended`, `March 28, 2026`, `Products`) as net-sales Products 80208;
shares-used Basic 14710718 and EPS Basic 4.87 likewise differ only by row
position. Header links alone cannot distinguish revenue from cost, or a share
count from a per-share amount. Corpus prevalence has not yet been measured.

Remediation options (not implemented): link amount rows to the nearest preceding
label-only group row within a bounded, indentation- or colon-aware policy, or
flag duplicated leaf labels as context-ambiguous. Add regressions and replay.

### WP33-REV-005: external units line missed; group labels recorded as unit hints

Status: **source units line confirmed by user (screenshot); unresolved**.

The units line is a separate paragraph between the title and the table (body
element 62; table at element 64). The extractor takes the title from nearby
blocks but does not capture this line: `scale_hint` is null and `unit_hints`
are `Earnings per share:` and `Shares used in computing earnings per share:` —
row-group labels, not units. JPMorgan candidates carried their units heading
inside the table, which is why candidate 1 retained it.

The line carries a three-way exception: amounts in millions, share counts in
thousands (so 14,710,718 means about 14.71 billion shares), per-share amounts
unscaled. No per-cell unit or scale is asserted, so no wrong value is emitted,
but the evidence needed for later resolution is absent from the table record
and its retrieval text. Corpus prevalence is not measured.

Remediation options (not implemented): capture a bounded units/scale paragraph
adjacent to the table (with locator) as a raw hint, and stop matching group
labels as unit hints. Mixed-unit application remains a later, versioned policy.

## Candidate 7: Apple Q2 FY2026 condensed consolidated balance sheets

Status: **partial review; table acceptance pending**.

- Accession: `0000320193-26-000013` (10-Q); same source SHA-256 as candidate 6.
- Table ID: `table:e5fcd2b551e50a80b21aaa1de8416a9797a75e311e78fd8529b683b0e9ea3f13`.
- Source DOM: `/*[1]/*[2]/*[84]/*[1]`; printed page 3.
- [Original filing](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm).
- [Extracted document](../.runtime/wp33/completion-documents/0000320193-26-000013.json).

Codex withheld extracted values before asking; the user's readings match:

1. Date headings: **March 28, 2026; September 27, 2025** (row 1, columns 3, 9).
2. Units line (location clarified by Codex, wording not supplied):
   **(In millions, except number of shares, which are reflected in thousands, and
   par value)**. Not captured; `unit_hints` empty, `scale_hint` null.
   WP33-REV-005 recurs.
3. Term debt, March 28, 2026: current **8,310**, non-current **74,404**.
   Decimals 8310 (row 26) and 74404 (row 30), both column 3. Both link only to
   `March 28, 2026` and `Term debt`; `Current liabilities:` / `Non-current
   liabilities:` are unlinked. WP33-REV-004 recurs (also `Marketable securities`
   current vs non-current), here distinguishing current from non-current debt.
4. Retained earnings/(Accumulated deficit): **12,359; (14,264)**. Decimals
   12359 and -14264 (row 39); the sign change across periods is preserved.
5. Total liabilities and shareholders' equity, March 28, 2026: **371,082**.
   Decimal 371082 (row 42, column 4).
6. Common stock row label matches exactly, including `$0.00001 par value`,
   `50,400,000`, `14,667,688 and 14,773,260`. The label is a row header with
   status `uncertain` and no value: embedded counts are not emitted as amounts.

Codex Decimal reasonableness checks on extracted values: total liabilities plus
equity equals total assets in both periods (264591 + 106491 = 371082;
285508 + 73733 = 359241); current assets components sum to 144114.
The table includes liabilities and equity, so `financial_statement` is
consistent with the source; WP33-REV-002 does not apply.

## Candidate 8: Apple Q2 FY2026 condensed consolidated statements of cash flows

Status: **partial review; table acceptance pending**.

- Accession: `0000320193-26-000013` (10-Q); same source SHA-256 as candidate 6.
- Table ID: `table:f3a4265e3b45d2dd423b33474794f94313d9f48560f010b75730d80b5eb85890`.
- Source DOM: `/*[1]/*[2]/*[104]/*[1]`; page following the balance sheet.
- [Original filing](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm).
- [Extracted document](../.runtime/wp33/completion-documents/0000320193-26-000013.json).

Codex withheld extracted values before asking; the user's readings match:

1. **Six Months Ended** over **March 28, 2026; March 29, 2025**; every amount
   links to the group and its date.
2. Units line: **(In millions)**. Not captured (`unit_hints` empty);
   WP33-REV-005 recurs, though this line has no exceptions.
3. Beginning balance, March 28, 2026 column: **35,934** (Decimal 35934, row 3).
4. `Other`, March 28, 2026: operating **(1,717)**, investing **(1,584)**,
   financing **(126)**; Decimals -1717, -1584, -126 (rows 10, 26, 36). All three
   link only to `Other`; section rows are unlinked. WP33-REV-004 recurs.
5. Investing: **(11,054); 12,709**; Decimals -11054 and 12709 (row 27).
6. Ending balance, March 28, 2026 column: **45,572** (Decimal 45572, row 40).

Codex verified that blank extracted rows 25 and 33 are blank in the source.
Decimal checks on extracted values: 82627 − 11054 − 61935 = 9638, and
35934 + 9638 = 45572. Cross-table: the beginning balance equals candidate 7's
September 27, 2025 cash (35934) and the ending balance its March 28, 2026 cash
(45572).

Period observation (existing limitation, not a new finding): the beginning
balance is an instant at the start of the six-month period, yet it links to
`Six Months Ended` / `March 28, 2026` like the duration amounts. Header links
must not be read as the measurement period; instant-versus-duration semantics
remain unresolved.

## Candidate 9: Apple Q2 FY2026 condensed consolidated statements of comprehensive income

Status: **partial review; table acceptance pending**.

- Accession: `0000320193-26-000013` (10-Q); same source SHA-256 as candidate 6.
- Table ID: `table:942934b96eb596f72366bf9abbe20395919adbde38d8d9e38aa92f40f93c5f93`.
- Source DOM: `/*[1]/*[2]/*[74]/*[1]`; page following the operations statement.
- [Original filing](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm).
- [Extracted document](../.runtime/wp33/completion-documents/0000320193-26-000013.json).

Codex withheld extracted values before asking; the user's readings match:

1. Units line: **(In millions)**. Not captured; WP33-REV-005 recurs.
2. Foreign currency translation: **67, 90, (92), (535)**; Decimals 67, 90, -92,
   -535 (row 5), each with correct group/date links.
3. Asked for the first-column value of both `Adjustment for net (gains)/losses
   realized…` rows; the user supplied all four values of the marketable-debt-
   securities row: **14, 185, 18, 405**, matching row 14. The derivative-row
   reading (row 9) was skipped at the user's request; it remains unreviewed. Both rows carry identical row-header text
   and no group link (WP33-REV-004 recurs).
4. Total other comprehensive income/(loss): **(521), 426, 196, 809**; Decimals
   -521, 426, 196, 809 (row 17).
5. Total comprehensive income: the user supplied all four values
   **$ 29,057; $ 25,206; $ 71,871; $ 61,919**, matching row 18; six months ended
   March 28, 2026 is **71871**.

Decimal checks on extracted values: 29578 − 521 = 29057; 71675 + 196 = 71871;
67 + 206 − 794 = −521. Net income (29578, 71675) matches candidate 6.

## Candidate 10: Apple Q2 FY2026 condensed consolidated statements of shareholders' equity

Status: **partial review; table acceptance pending**.

- Accession: `0000320193-26-000013` (10-Q); same source SHA-256 as candidate 6.
- Table ID: `table:a0f8b957b8da8a39164833973f57574fe1bc69afa3f00e0a1a246fbdd1265e1e`.
- Source DOM: `/*[1]/*[2]/*[94]/*[1]`.
- [Original filing](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm).
- [Extracted document](../.runtime/wp33/completion-documents/0000320193-26-000013.json).

The user confirmed the displayed values: beginning equity **88,190; 66,758;
73,733; 56,950**; net income **29,578; 24,780; 71,675; 61,110**; ending
equity **106,491; 66,796; 106,491; 66,796**; and dividends per share or RSU
**0.26; 0.25; 0.52; 0.50**.

The user corrected the period labels: **Three Months Ended** for the first two
columns and **Six Months Ended** for the last two, paired respectively with
March 28, 2026 and March 29, 2025. This confirms selected displayed values and
period-column reading only; whole-table acceptance, units/scale, period
semantics, and classification remain pending.

## Candidate 11: Microsoft FY2025 income statements

Status: **partial review; table acceptance pending**.

- Accession: `0000950170-25-100235` (10-K).
- Source SHA-256: `bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665`.
- Table ID: `table:9c94032b4c078f61443b37e0329f309d40bde32d41e2a50442188f4e650ccc41`.
- Source DOM: `/*[1]/*[2]/*[199]/*[4]`.
- [Original filing](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm).
- [Extracted document](../.runtime/wp33/completion-documents/0000950170-25-100235.json).

The user confirmed the displayed **Year Ended June 30, 2025 / 2024 / 2023**
headings, **(In millions, except per share amounts)** units line, and selected
displayed values in that year order: total revenue **281,724 / 245,122 /
211,915**; gross margin **193,893 / 171,008 / 146,052**; operating income
**128,528 / 109,433 / 88,523**; other income (expense), net **(4,901) /
(1,646) / 788**; net income **101,832 / 88,136 / 72,361**; basic EPS
**13.70 / 11.86 / 9.72**. This was an assisted confirmation after Codex showed
the values. The user corrected Codex's page claim: total revenue and the units
line are on printed page 50, while the statement continues on page 51.

The confirmation applies to the visually reconstructed entries. It does not
assert successful normalization of the two parenthesized other-income values;
see WP33-REV-006. Whole-table acceptance remains pending.

### WP33-REV-006: accounting parentheses split across adjacent source cells

Status: **confirmed source-linked normalization gap; unresolved**.

In candidate 11, 2025 `Other income (expense), net` has raw `(4,901` at row 29,
column 3 and raw `)` at column 4. The 2024 cells contain `(1,646` and `)` at
columns 7 and 8. The extracted amount cells are `uncertain` with `value=null`;
the closing-parenthesis cells are `not_numeric`. The user's displayed readings
confirm the negative entries, but the structured extraction does not emit
`-4901` or `-1646`. Candidate 12's `Accumulated other comprehensive loss` row
shows the same pattern for `(3,347)` and `(5,590)`; those two displayed values
have not been independently reviewed by the user.

The single-cell normalizer correctly abstains on incomplete tokens. A future
bounded source-linked policy must join or otherwise resolve paired sign cells,
preserve both source cell locators, and abstain on unmatched or ambiguous pairs.
No repair or corpus prevalence estimate is recorded.
