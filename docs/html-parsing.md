# Deterministic HTML parsing — WP3.2

Architecture 3.1. WP3.2 implements bounded HTML parsing under ADR-003 using
preserved primary-document bytes. Physical Silver publication, XBRL
normalization and retrieval remain later packages. WP3.3 consumes these
unchanged blocks through [structured table extraction](table-extraction.md),
including unclassified/ambiguous sections; numeric normalization is still pending.

## Entry points and contracts

`processing.html.parse_html(fetch, body)` performs no I/O. The caller supplies a
Phase 2 `Fetch` and the original Bronze bytes. `validated_source` revalidates the
fetch, rejects quarantine and checks the original byte count and SHA-256. The
caller must also verify the immutable stored manifest. The corpus command below
does both. Phase 2 acquisition and all `canonical-1` rows remain unchanged.

The frozen `contracts.parsing.ParsedDocument` envelope (`html-result-1`) contains
the existing `CanonicalFiling`, `DocumentVersion`, `Section`, `ContentBlock`,
`QualityEvent` and `SourceProvenance` records. Its validator checks source equality,
document ownership, section partitioning, contiguous ordinals, block assignment,
normalized document hash, quality/provenance references and pipeline consistency.
Revalidate this envelope when reading its JSON. It is a diagnostic interchange
format, not a dataset publication or a replacement for canonical storage schemas.

`parse_batch` yields either a validated document or a `ParseFailure` with fetch ID,
source checksum, safe reason code and quarantine disposition. Rejection affects
only that input. Integrity errors produce no document/section records.
Unexpected programming/contract errors propagate.

## Decoding, recovery and content ownership

The runtime dependency is pinned `lxml==6.1.3`; development uses
`lxml-stubs==0.5.1`. See [lxml recovery semantics](https://lxml.de/parsing.html).
The parser receives an in-memory string, disables network loading and installs a
resolver that rejects external resource requests. It never renders or executes
HTML, JavaScript, styles, XSLT or XInclude.

Decoding precedence is BOM, explicit charset/XML encoding in the first 4096 bytes,
strict UTF-8, then Windows-1252 with a warning. The accepted encodings are UTF-8,
UTF-16 variants, ASCII, Windows-1252 and Latin-1. Unsupported declarations and
invalid byte sequences take the documented fallback, with replacement recorded
when necessary. Source bytes and their checksum never change.

Whitespace collapses to one space; zero-width spaces and BOM characters are
removed from normalized text. DOM traversal emits each visible text node once,
with parent text, nested blocks and tails kept in order. Native headings, short
emphasized SEC labels, paragraphs and list items become separate blocks. Native
heading level and original styling remain recoverable through the source DOM;
there is no separate inferred heading-tree schema in this package.

Scripts, styles, templates, hidden elements and inline-XBRL header/resources are
excluded. Visible inline-XBRL values remain visible text without financial
interpretation. Stylesheet classes, generated CSS content and full browser layout
are not evaluated. Narrative footnotes survive in their ordinary source blocks;
dedicated financial footnote semantics belong to table processing.

Every ordinary or nested table is one opaque `[TABLE]` block, with its original
table locator. Its cells, figures, captions and nested tables are not emitted as
narrative. A narrowly recognized short item/part heading table is a layout heading:
at most three rows, four nonempty cells, no nested tables, one item label and no
pure numeric cells. This supports Amazon headings while retaining numeric tables.
Unsupported tables remain available in Bronze for WP3.3.

Hard limits are 32 MiB input, 750,000 recovered nodes, depth 240 and 100,000 blocks;
libxml2's own safety limits also remain enabled. Resource violations reject the
document instead of returning a truncated result. There is no independent
process watchdog or measured worst-case memory/CPU guarantee. HTML recovery can
lose severely malformed content; a recovery warning is not proof of completeness.
libxml2 error logs can be capped, so the warning records presence rather than an
exhaustive count of repairs.

## Form-aware classification

`sec-sections-1` recognizes labels within extracted DOM blocks; it does not split
raw HTML with regex. It combines native/emphasized headings, conventional SEC
titles, form-specific allowed items, reading order, part context and duplicates.
10-K items identify their standard part. A classified 10-Q item requires explicit
Part I/II context. Missing context, invalid form/item combinations, uncertain
headings and backward item order remain ambiguous with quality events.

Navigation/link text is not a body boundary. Multi-item TOC tables stay opaque.
Dense unlinked label runs repeated later in the body are retained as TOC content.
Bare repeated item labels remain running headers; accepted section labels are not
duplicated. Signatures, cover material, part preambles and otherwise unclassified
material remain in the ordered block partition. Missing priority items produce
document-level warnings. Sections describe contiguous physical source ranges;
incorporation-by-reference does not move distant annex material into an item.

## Provenance and reproducibility

Every section and block resolves through `document_id` to the document's immutable
source reference, containing normalized CIK, accession, filename, source URL,
original SHA-256 and byte count. The document carries parser/pipeline versions;
its provenance row preserves fetch ID/time and the canonical filing relationship.
The envelope validates these links without duplicating source fields on every row.

DOM paths use numeric element positions, such as `/*[1]/*[2]/*[17]`, to avoid
arbitrary inline-XBRL namespace bindings. They address the recovered, **unmodified**
DOM obtained from the original bytes with this parser version. Comments are not
counted as elements. They are not byte offsets or browser-generated XPath IDs.

Blocks have zero-based contiguous reading-order ordinals. Section first/last
ordinals are inclusive and together cover every block exactly once. Locator
`start`/`end` are half-open Unicode character offsets into the named normalized
document representation: block texts joined with one newline, including table
markers. `text_sha256` names that representation. The element path identifies the
source owner even when mixed content produces multiple text fragments from it.

Parser identity includes `sec-html-1`, actual lxml/libxml versions and classifier
version. Pipeline version is `html-1`; canonical records retain `canonical-1` and
`id-1`. Backend changes create a different parser identity. `logical_bytes()` uses
canonical sorted UTF-8 JSON and excludes the separate fetch-occurrence provenance
row. Identical bytes, source metadata and parser version produce the same logical
result even after another fetch. Fetch timestamps do not influence document IDs.

## Reproduction and evaluation

From the repository root, with the existing local Bronze corpus:

```bash
bash scripts/uv.sh run --frozen python -m sec_research.processing.corpus \
  --split development --output .runtime/wp32/development.json
```

`--split all` or `--split held_out` deliberately includes reserved cases. The
default is development only. Do not tune using held-out predictions or labels.
The command checks every stored manifest/object against the independent inventory
before and after parsing. It never acquires SEC data or modifies Bronze, and
refuses diagnostics output inside the artifact root. It validates each output,
resolves every block locator, checks offsets, replays parsing and writes diagnostic
JSON documents beside the report. Errors cause a nonzero exit.

The [frozen split](../tests/fixtures/parsing/corpus-split.json) reserves eight newer
filings; the ten earliest company/form filings are development. The
[annotation file](../tests/fixtures/parsing/boundaries.json) has selected start and
next-section source XPath anchors, headings, hashes and annotation provenance.
Labels were manually selected by Codex from source DOM inspection independently
of predictions. **They have not been adjudicated by an independent human.**
The [freeze](../tests/fixtures/parsing/heuristic-freeze.json) records algorithm/lock
hashes before held-out source annotation/evaluation. The test suite guards it.

Exact-boundary match means both the first block at the annotated source heading
and the last block immediately before the next source heading match. Each chosen
item is one denominator, not two successes. Unlabeled sections and missing implicit
headings are not included in this metric. Structural detection counts, parsing
success, warnings and failures are reported separately by form/company/section.
Do not describe parsing success as section accuracy. See the
[package review](phase-3-wp3.2-review.md) and
[measured diagnostics](phase-3-wp3.2-diagnostics.json).
