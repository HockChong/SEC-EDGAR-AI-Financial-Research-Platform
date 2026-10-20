# WP3.2 source review and regression fixtures

`corpus-split.json` freezes all 18 original Bronze document hashes into ten
development and eight held-out filings. All companies have a development 10-K and
10-Q; newer filings are reserved. The split was written before heuristic work.

`boundaries.json` records 25 selected item ranges across seven documents: 18 ranges
in five development documents (all companies) and seven ranges in two held-out
documents (Apple 10-Q, Microsoft 10-K). Each label identifies the original source
hash, form-aware item, start XPath, next-section XPath and exact source headings.
Ends include intervening page headers until immediately before that next heading.
The annotated items cover all seven prioritized form/part/item types.

Codex selected anchors by inspecting original DOM headings and nearby disclosure
text, independently of parser predictions. This is agent-authored manual source
review; no human annotator or independent human adjudication is claimed. These
selected labels cannot establish whole-document precision, whole-corpus section
accuracy or generalization. JPMorgan's unclassified quarterly Part I content is
reported as a known coverage gap, outside the selected labeled denominator.

`heuristic-freeze.json` captures the algorithm and lock before held-out source
inspection. Hashes normalize CRLF to LF. Offline tests prevent unnoticed heuristic
changes. Held-out evaluation was run once after this freeze; do not repeatedly
tune using its expected labels. Future changes need a new development/evaluation
protocol and must preserve this baseline.

The three small `.htm` files are **synthetic assemblies of real source elements**
with synthetic separators. `excerpts.json` attributes original accessions, hashes
and element paths and checksums the exact excerpt bytes. They exercise Amazon
heading tables, Microsoft running headers and JPMorgan missing-part ambiguity.
They are offline regression inputs, not original Bronze artifacts or substitutes
for the 18-document smoke test. Test source metadata is explicitly synthetic.

Original filings and full parsed outputs stay under ignored `.runtime/`.
`docs/phase-3-wp3.2-diagnostics.json` is the small reproducible measurement report;
see `docs/html-parsing.md` for the runner and metric definitions.
