# WP3.3 table fixtures and review candidates

`multi-period.htm` is wholly synthetic and fictional. It contains three header
rows and two data rows, with separate three-month/six-month groups, merged date
headings and comparative years. The project owner writes the main association
assertions in `exercises/wp33/test_headers.py`; the production provenance test
only checks source resolution, round-trip validation and deterministic replay.

`review-cases.json` contains 25 diagnostic candidates from the immutable local
SEC Bronze corpus. Original SEC URLs, CIKs/accessions, original source SHA-256,
DOM paths and extracted sample cells identify each source. Predictions are
not expected labels: human adjudication is pending and expected structure and
financial interpretation remain null. Cases cover five companies and both
JPMorgan quarters whose section classification remains incomplete.

The generating command is documented in `docs/table-extraction.md`; full
diagnostic outputs remain under `.runtime/wp33/final-documents` and are excluded
from Git. `docs/phase-3-wp3.3-adjudication.md` is the human review checklist.
No benchmark score may treat these predictions as financial ground truth.
