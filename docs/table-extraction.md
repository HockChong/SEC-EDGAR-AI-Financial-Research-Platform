# WP3.3 financial table extraction

Architecture 3.1 / ADR-003. Structural extraction, displayed-number normalization,
and multi-period regression tests are implemented. Hands-on assignments are paused;
Codex maintains the implementation. Acceptance requires package review and independent
adjudication. No XBRL concept mapping, embeddings, LangChain,
dataset publication or later-phase implementation is included.

## Contracts and entry point

`processing.tables.extract_tables(fetch, body)` is a pure offline function. It
reuses `parse_html` for source SHA-256/length/filing validation, document identity,
and original section/block ownership. It recovers the same unmodified DOM with
the existing bounded, network-disabled lxml parser. The caller must separately
audit the stored manifest; the corpus command does so before and after processing.

`contracts.tables.TableExtraction` (`table-result-2`, extractor `sec-tables-2`)
contains the original document, source blocks/sections, table results and a
separate tuple of `TableText` records (`table-text-2`). Canonical `StructuredTable`
and `TableCell` rows remain `canonical-1`; the existing table's `retrieval_text`
field is deliberately empty. Text rendering never participates in canonical table
or cell identity. Storage schema families, dependencies and the WP3.2 heuristic
freeze remain unchanged. This envelope is diagnostic interchange, not Silver.

Each table retains its source DOM path and block/section references. Nested
tables additionally reference the parent table path. Their source cells are
extracted separately; the outer cell uses `[NESTED TABLE]` in place of descendant
table text, preventing duplicated amounts. The retained original bytes are the
authority for literal markup. Raw cell text means visible lexical text, with
whitespace retained and `<br>` represented as a space; it is not serialized HTML.
Hidden content follows the WP3.2 exclusions. CSS classes and browser layout are
not interpreted.

The envelope checks identity, table ownership, source-order cell preservation,
grid bounds, overlaps, header links, normalization state and financial retrieval
coverage. `logical_bytes()` is sorted canonical JSON without fetch timestamps.
CIK, accession, filename, original URL, source SHA-256 and parser version are
reachable through the document's source reference. IDs include processing
versions and canonical content. Fetch-occurrence provenance remains in the
existing WP3.2/Phase 2 records; no duplicate fetch catalog is introduced.

## Placement and interpretation rules

All visible DOM tables are enumerated, including WP3.2 layout-heading tables and
tables in classified, ambiguous and unclassified sections. Classification is a
versioned heuristic with explicit warnings: TOC label/link evidence, statement
title plus numeric-shaped cells, financial vocabulary plus numeric-shaped cells,
small layout tables, then an uncertain narrative fallback. Categories are useful
diagnostics, not independently measured financial/nonfinancial ground truth.

The grid preserves each source `<td>`/`<th>`, including spacer, currency-symbol,
parenthesis and blank cells. It does not concatenate adjacent amounts. Rowspan
and colspan establish occupied coordinates. A rowspan occupies later-row slots;
subsequent cells skip those slots at their starting position. A span rectangle
that intersects another cell is quarantined instead of shifted sideways.
`rowspan=0` extends through its explicit or implicit row group. Invalid spans,
cross-group/out-of-range spans, excessive dimensions and cells outside rows retain
raw source cells and warnings but produce no asserted canonical grid.
Limits are 512 columns and 200,000 logical slots per table, in addition to the
existing document size/node/depth limits. Ragged grids retain holes, with a warning.
Empty tables are retained as quarantined entries, not invented 1x1 tables.

Leading explicit header rows and period-label rows establish column headings;
explicit row scopes and labels before numeric-shaped cells establish row headings.
Header IDs attach only where the data cell is fully covered by the header's
column span. Header rows remain ordered, preserving hierarchy and duplicate-text
source identities. Headers have no outgoing ID edges to avoid circular
content-addressed IDs. Full calendar intervals, quarter-versus-YTD semantics,
unit application, row-spanning subcategory semantics and visual alignment remain
unverified. An unresolved association remains unknown and is never filled from
the filing date. This is not a browser table-layout engine.

Titles come from captions, short statement-title cells or nearby preceding blocks,
stopping at intervening tables. Unit/scale labels remain raw hints; mixed units
such as "millions except per share" do not become a global scale. Superscripts
and local anchor text preserve footnote markers without attempting footnote-body
resolution. Malformed HTML recovery warnings are carried forward; successful
placement in the recovered DOM does not prove that recovery preserved every
original malformed node.

`normalize_table_number(raw_text, *, context)` uses `table-numeric-1`: ASCII
digits, correctly grouped thousands commas, optional decimal fractions, one
leading sign or accounting parentheses, and an optional trailing percent sign
after the number or closing parenthesis. Decimal values retain displayed magnitude;
there is no scale multiplication, percent division, float conversion, or arithmetic
rounding. Original lexical text is unchanged. Empty text and lone ASCII/en/em
dashes are missing under this policy, never zero; their real financial meaning
still requires adjudication. Labels without digits are `not_numeric`. Other
digit-containing formats are `uncertain`, including currency symbols, Unicode
minus, locale formats, scientific notation and attached footnotes. Numeric DOM
footnotes also force abstention, even when concatenated text looks like a number.

Every reconstructed cell has a completed lexical result. `normalization_complete=true`
means this processing step ran; it does not certify financial correctness, complete
coverage of quarantined raw cells, or resolved context. Canonical cells use `empty`
only for blank missing text; nonblank missing dashes remain `uncertain` with explicit
`missing` context. Cell values/status and normalization results must agree. Nonfinite
values, floats, contradictory flags, and pending scaffold states are rejected.
`NumericContext` copies evidence-backed currency/unit/scale when supplied directly;
the extractor currently supplies unknown context because table hints can mix units.
Numeric headers such as years are lexical numbers, not financial observations.
Adjacent symbol/sign cells are not consolidated into amounts. These records must
not be used as selected financial facts without later context resolution.

Retrieval text includes company CIK, accession, form, title, raw values, raw unit
labels, header/period labels, table/cell IDs and original source/DOM references.
It explicitly distinguishes displayed-number parsing from financial verification. The company CIK is
used because the filing `Fetch` contract has no authoritative legal-name field.
Only classified financial tables with reconstructed grids receive retrieval text;
all other tables remain available in structured/raw results. Heuristic false
negatives are a known retrieval limitation pending adjudication.

## Diagnostics and adjudication

```bash
bash scripts/uv.sh run --frozen python -m sec_research.processing.table_corpus \
  --output .runtime/wp33/diagnostics.json
```

This command audits every local Bronze object/manifest, processes every stored
primary filing (all 18 in the current inventory), replays extraction, revalidates
JSON envelopes, independently enumerates source DOM tables/cells and resolves
their paths and raw lexical text. It writes full documents beside diagnostics,
plus approximately five review candidates per company in `diagnostics-samples.json`.
No SEC downloads occur. Output inside immutable Bronze storage is rejected.
The command's zero exit means diagnostics completed, **not WP3.3 acceptance**.

Review candidates include statement families, merged/multi-period cases and both
problematic JPMorgan 10-Qs. Their classifications and shapes are predictions;
expected structural and financial judgments are deliberately null. A human must
inspect the original source, record corrected spans/headers/periods, distinguish
missing from zero, interpret units/footnotes and accept/reject each candidate.
Neither these candidates nor successful parsing supply accuracy, precision or
recall. All-filings diagnostics include the prior held-out filings but do not
change WP3.2 labels, split, freeze or heuristics; they are not a new blind benchmark.

Current v2 review candidates are in the [completion manifest](phase-3-wp3.3-completion-candidates.json).

See the [implementation review](phase-3-wp3.3-acceptance-review.md) for measured outcomes and
the [preserved exercises](../exercises/wp33/README.md) for optional practice.
