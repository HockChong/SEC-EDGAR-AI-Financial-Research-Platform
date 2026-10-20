# Bronze corpus expansion review

Review date: 2026-10-20. Architecture: 3.1. Scope: bounded Bronze corpus
expansion and validation only. **Acceptance satisfied: 18 filings across five
companies**, with no missing or failed selected artifacts.

## Result and files

- Apple, Microsoft and Alphabet: each has two 10-Ks and two 10-Qs.
- Amazon and JPMorgan Chase: each has one 10-K and two 10-Qs.
- Total: **8 annual and 10 quarterly filings**, five submissions responses and
  five Company Facts responses: **28 fetch records, 28 unique objects, zero orphans**.
- Original source bytes: **114,345,283 bytes**. Immutable fetch manifests:
  **26,013 bytes**. Total Bronze file payload size: **114,371,296 bytes**.
  These sizes exclude PostgreSQL, filesystem allocation overhead, previews,
  staging, build artifacts and caches.
- The original three Apple fetch records, manifests and objects remain intact.
  Added 17 filing bodies, four submissions responses and four Company Facts
  responses. No history-file download was necessary.

Created these small review artifacts; downloaded bodies remain Git-ignored:

- [Proposed ingestion manifest](bronze-corpus-proposed.json): actual accessions,
  primary filenames, forms, filing/report dates, source URLs, estimated missing
  downloads and expected content-addressed paths. Written before filing acquisition.
- [Verified Bronze inventory](bronze-corpus-inventory.json): all fetch IDs, source
  metadata, checksums, byte counts, actual object URIs, identity checks and totals.
- [CLI execution evidence](bronze-corpus-runs.json): exact argument vectors,
  run IDs, exit statuses, summaries and safe logs for both 18-command passes.
- This review. Temporary operational discovery, CLI-driving and verification
  scripts and snapshots are under ignored `.runtime/`.

Existing uncommitted Phase 2/WP3.1 changes were preserved on the current `main`
checkout. No application, test, configuration, architecture or dependency files
were edited by this package. Nothing was staged, committed, pushed or published.

## Selection, contracts and decisions

Read AGENTS, requirements, Phase 2/WP3.1 reviews, ingestion/development guidance,
roadmap, data architecture, testing/evaluation strategies and ADR-003/010.
Inspected CLI, discovery, payload contracts, acquisition, PostgreSQL coordination,
local immutable storage, settings and existing manifests before acquisition.
Initial CLI reconciliation verified three fetches/objects and zero orphans.

Selected the newest required number of each form from official submissions data,
bounded through 2026-10-20. Apple annual reports span filing years 2024 and 2025;
Microsoft and Alphabet annual reports span 2025 and 2026. Quarterly report dates
span multiple periods in 2026. The existing Apple accession
`0000320193-26-000020` is eligible and was reused.

Discovery reused `discover_filings`, `Acquisition`, `SecClient`, `PostgresLimiter`,
`PostgresManifest` and `LocalBronze`. Its initial lower filing-date bound was
2024-01-01; JPMorgan was narrowed to 2026-01-01 after the configured ten-history-file
bound rejected the broader window. All JPMorgan targets exist in recent submissions.
No bound was raised and no entire historical archive was ingested.

The supported CLI has no form/accession selector. Instead, each proposed filing
was verified to be the only eligible filing on its filing date, then acquired
through an inclusive one-day CLI window with `--max-filings 1`. This achieves the
requested form mix without downloading intervening filings or changing the pipeline.
Company Facts was enabled; repeated requests reused its fresh cached bytes.

The real SEC identity already present in the process environment was used without
printing or recording it. All acquisition was serial with
`SEC_REQUESTS_PER_SECOND=1`, sharing the existing development PostgreSQL coordinator
and `.runtime/artifacts` root. No refresh was requested. TLS, response budgets,
bounded retries and create-only publication remained enabled. Current
[SEC fair-access guidance](https://www.sec.gov/about/developer-resources) and
[API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
were checked. No new ADR or implementation approval was needed: no defect blocked
the supported pipeline.

## Commands and measured verification

Commands ran from this checkout. Native Python commands used
`.venv/Scripts/python.exe` (3.12.14); shell scripts used
`C:/Program Files/Git/bin/bash.exe`. The public disposable local development
database URL from `docs/development.md` was supplied explicitly, with the existing
artifact root. No private identity value is reproduced here.

- `python .runtime/expand_corpus.py`: successful final discovery wrote the proposal.
  Earlier discovery attempts failed as described below; they are not successes.
- `python .runtime/ingest_corpus.py first`: **18/18 CLI invocations exited 0**,
  each with one successful/reused filing, one successful/reused Facts acquisition
  and an empty errors list. Exact per-filing commands are in the execution evidence.
  The first pass made **21 new HTTP downloads**; discovery had already acquired
  the four missing submissions responses. One invocation's shape is:

  ```bash
  python -m sec_research.ingestion.cli ingest \
    --company 0000320193 --from-date 2025-10-31 --to-date 2025-10-31 \
    --max-companies 1 --max-filings 1 --max-history-files 10
  ```

- `python .runtime/verify_corpus.py`, before and after replay: passed. Independently
  recomputed every object's SHA-256 and byte count; validated all source envelopes;
  compared filing metadata with the stored SEC submissions rows; checked source URL
  identity and embedded `dei:EntityCentralIndexKey`/`dei:DocumentType` in all 18
  documents. Period-end text was recorded as source text, without financial parsing.
  Original Apple fetch metadata matched the initial snapshot exactly.
- `python .runtime/ingest_corpus.py repeat`: **18/18 exited 0**, empty errors and
  empty acquisition logs, **zero SEC response events**. The complete mapping of
  object/manifest paths to independently computed hashes was unchanged. Fetch and
  object counts remained 28. Operational run records were appended as designed.
- `python -m sec_research.ingestion.cli reconcile`: final **28 fetches,
  28 objects, 0 orphans**, exit 0; no network access or repair.
- `bash scripts/check.sh`, with `TEST_DATABASE_URL` pointing only to dedicated
  `sec_research_test` and `PYTEST_ADDOPTS='-o cache_dir=.runtime/pytest-corpus'`:
  **passed**. Locked 42-package resolution, Ruff lint, format (49 files), strict
  mypy (47 source files); **200 tests passed in 12.65 seconds**, 0 failed,
  0 skipped, 0 expected failures, 93% branch-aware coverage. Integration fixtures
  created/dropped uniquely named temporary databases, not the development corpus.
- `bash scripts/verify-wheel.sh`: **passed** after package-registry access was
  available. Built wheel/sdist, installed 23 locked runtime dependencies with hash
  checks and validated typing marker, canonical contracts, API and ingestion CLI
  outside the checkout.
- `git diff --check`: passed. Reviewed changed-file scope and safe log contents;
  dependency/lockfiles have no diff. Raw Bronze bodies and operational scripts
  remain ignored. No credentials or contact identity were added to review artifacts.

## Failures, limitations and next package

No selected artifact remains missing, quarantined or failed. Initial sandbox SEC
network access failed with `network_failure`; discovery succeeded with network
access. JPMorgan's first broad discovery returned `invalid_metadata` because more
than ten history files overlapped; narrowing its window resolved this without code
changes. Failed discovery runs remain recorded as failed operational history.
Initial wheel validation could not reach PyPI (socket access denied); the authorized
network retry passed without changing pins, TLS or hash verification. Git emitted
a nonblocking warning about the protected global ignore file.

All successful records are `unprocessed`. Identity checks establish company/form,
URL and submissions metadata consistency; they do not establish parsing accuracy,
financial correctness, section/table extraction or XBRL semantic coverage. Company
Facts is one current response per company, not a reconstructed historical API view.
The corpus contains primary documents, not exhibits, amendments or all XBRL files.
It is a representative development corpus, not a labeled evaluation benchmark.

Existing local-storage immutability, retention, backup and reconciliation limitations
in the Phase 2 review still apply. Hosted CI, deployment, throughput benchmarks,
backup recovery and Silver/Gold/RAG/agent evaluations were unrun and are not claimed.
No new automated tests were added because no runtime logic changed; full existing
regression and direct live integrity/replay checks cover this operational package.

All corpus-expansion acceptance criteria are satisfied. Recommended next package:
separately authorized **WP3.2 deterministic HTML parsing and form-aware section
extraction**, using this preserved corpus. Stop here; WP3.2 has not started.
