# Synthetic SEC acquisition fixtures

These hand-authored fixtures contain fictitious company identity and financial values.
They were created for offline tests, not downloaded from the SEC. No real-company
financial conclusions or live-access evidence may be derived from them.

Envelope shapes follow the [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).
Synthetic source URLs are constructed from CIK `0000000001`, accessions in the fixtures,
and official endpoint templates. Tests verify SHA-256 against the exact fixture bytes
and preserve the lexical Company Facts decimal without financial interpretation.

`manifest.json` records the fixture byte counts, SHA-256 values and synthetic source
URLs. `.gitattributes` disables newline conversion for these byte-identity fixtures.
