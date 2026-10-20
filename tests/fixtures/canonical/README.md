# Canonical contract fixtures

All files here are small, hand-authored synthetic examples, not SEC downloads or
real issuer financial results. Source URLs in `manifest.json` are illustrative
Phase 2-compatible identities; tests never request them. CIK 0000000001 is used
only as a synthetic identifier.

- `annual.htm`: 10-K Items 1, 1A, 7 and 8; duplicate TOC labels; ordered paragraphs,
  list, table, merged headers, an empty cell, parentheses, millions and footnotes.
- `quarter.htm`: 10-Q Parts I and II; repeated Item 1, Item 2 MD&A and Item 1A risk;
  quarterly versus YTD table headers and thousands.
- `malformed.htm`: unclosed elements, irregular cells, an uncertain heading and
  inert external-resource/script traps. No HTML parser is implemented in WP3.1.
- `company_facts.json`: exact fractional values, negative amounts, duplicate source
  observations, a later comparative disclosure, amendment, USD/EUR, instant,
  quarterly/YTD/52-week/53-week intervals, and one deliberately reversed period.
  Missing dimensions remain unknown. Later comparatives do not establish a formal
  restatement. The invalid observation must eventually produce a quality event.

`manifest.json` pins exact byte lengths/checksums and expected source identities.
Contract tests construct expected records explicitly from these finite examples;
they do not implement a general parser, normalizer or selection policy.
Broader real-world coverage and parser boundary annotations belong to WP3.2–3.4.
