# SEC EDGAR Bronze ingestion

Phase 2 implements acquisition only. Source HTML and API JSON remain original bytes;
HTML parsing, XBRL normalization, retrieval and agents belong to later phases.
See the [package review](phase-2-review.md) for automated verification and the bounded user-executed live acceptance evidence.

## Setup and CLI

Use Python 3.12.14, the locked environment and the existing PostgreSQL service. Run
these commands from the repository root in Bash (Git Bash on Windows):

```bash
bash scripts/setup.sh
export DATABASE_URL='postgresql+psycopg://sec_research:sec_research_dev@127.0.0.1:5432/sec_research'
bash scripts/uv.sh run --frozen alembic upgrade head
bash scripts/uv.sh run --frozen python -m sec_research.ingestion.cli --help
```

Set `SEC_USER_AGENT` in your process environment to your real organization/project
name followed by a real contact email. It is mandatory for acquisition, omitted from
logs and run configuration, and never fabricated by the application. No SEC API key
is required. The application does not load `.env` automatically.

After configuring the real identity, the following is an **optional live smoke run**,
separate from all deterministic tests. The user later ran the same one-company/one-filing
flow without an upper date bound; it passed ingestion, reuse and reconciliation on
2026-10-20. Exact commands and scope are recorded in the package review:

```bash
bash scripts/uv.sh run --frozen python -m sec_research.ingestion.cli ingest \
  --company 0000320193 --from-date 2025-01-01 --to-date 2026-10-20 \
  --max-companies 1 --max-filings 1 --max-history-files 10
bash scripts/uv.sh run --frozen python -m sec_research.ingestion.cli reconcile
```

Repeat the identical ingest command to resume failures or reuse successful sources.
CI substitutes synthetic SEC responses and uses temporary PostgreSQL databases and
artifact directories; it never calls the SEC. Do not use the synthetic test contact
or fixture company as a live identity or a real-company corpus.

`--company` accepts a CIK, exact ticker, or exact current name from the official SEC
ticker catalog; repeat it for multiple companies. CIK lookup also supports entities
absent from that catalog. Names/tickers must resolve uniquely; fuzzy search is not
implemented. Numeric CIKs are canonicalized to ten digits. CIK plus accession identifies
a filing; its archive URL includes the primary document name. Amendment forms
`10-K/A` and `10-Q/A` require `--include-amendments` and retain distinct accessions.

Date bounds are inclusive **filing dates**, not measurement periods. Discovery reads
recent filings and every referenced historical submissions file overlapping those
bounds. It does not treat recent submissions as complete history. Metadata conflicts,
unsafe filenames, malformed dates, or misaligned columns fail explicitly.

The newest `--max-filings` matching filings per company are selected deterministically.
Defaults are five company arguments, twenty filings per company and one hundred
historical files per company; integer limits must be 1–1000. Too many company arguments
or historical files is an error, not silent truncation of discovery. At most one
submissions request plus the selected history requests precedes filing downloads.
Company Facts is included once per company unless `--without-facts` is given. A Facts
404 is a recorded failure, not invented financial data.

The CLI emits a JSON summary with run ID, successful/reused filing and Facts counts,
and safe error codes. Exit 0 means success, 1 means acquisition/integrity/database or
partial failure, and 2 means invalid CLI/configuration. `--help` requires no database
or identity. `reconcile` requires a migrated database but no SEC identity or network.

## Access policy and bounds

The [SEC developer guidance](https://www.sec.gov/about/developer-resources), checked
on 2026-10-20, states an aggregate maximum of ten requests per second across machines.
The application caps its own aggregate starts at five per second and defaults to
serial acquisition. Every CLI process must share the **same PostgreSQL database**
for rate coordination. Other applications/databases using the same SEC access budget
must be coordinated operationally; this database cannot govern external traffic.

The [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
defines the padded-CIK submissions and Company Facts endpoints and historical-file
references. The client allows only those paths, the official ticker catalog and
filing archive paths over verified HTTPS. It follows no redirects, uses no ambient
HTTP proxy, requests identity encoding, and rejects unexpected compression. Checksums
cover the exact returned HTTP entity bytes after transfer framing, without decoding,
JSON serialization, newline conversion, or HTML rewriting. Responses over the byte
budget are rejected before Bronze publication. Invalid complete responses are retained
as quarantined source versions; interrupted/truncated transport bodies are never successes.

Process variables for transport configuration:

- `SEC_USER_AGENT`: required real organization/project and contact email.
- `SEC_REQUESTS_PER_SECOND`: default 5; greater than zero and at most 5.
- `SEC_TIMEOUT_SECONDS`: default 15; per-attempt connection/request/body budget, at most 60.
- `SEC_DEADLINE_SECONDS`: default 120; total request/retry/rate-wait budget, at most 600.
- `SEC_MAX_ATTEMPTS`: default 4; range 1–8, including the initial HTTP attempt.
- `SEC_MAX_BYTES`: default 33554432; range 1–134217728.
- `ARTIFACT_ROOT`: default `.runtime/artifacts`; keep it stable across resumptions.
- `DB_POOL_SIZE`: ingestion needs at least 2; default 5. A source lock holds one
  connection while metadata and rate coordination use another.

HTTP 429 and 500/502/503/504 plus transient transport failures use bounded exponential
backoff and injected jitter. Integer or HTTP-date `Retry-After` is a lower bound on
the next attempt's delay; a delay exceeding the remaining budget aborts the request.
403 and other permanent HTTP failures are not retried automatically. Access denial,
exhausted rate-limit retries, or deadline exhaustion stop the entire CLI run. Ordinary
per-filing failures allow other filings to complete. Neither identities nor IPs rotate.
The local embedded-client limiter coordinates threads/clients in one process; callers
running multiple processes must explicitly use `PostgresLimiter`, as the CLI does.

## Storage, identity and recovery

Objects use `ARTIFACT_ROOT/bronze/sha256/<first-two>/<sha256>`. Full downloads are staged,
fsynced, published by atomic create-only hard link, then verified. Existing objects
are compared and never replaced. Use a local filesystem supporting atomic hard links
(NTFS and ordinary Linux filesystems); unsupported filesystems fail rather than fall
back to overwriting. The root is trusted application-owned local storage. This is
application-level immutability, not administrator-proof archival/WORM storage.

Immutable fetch manifests use `bronze/manifests/<fetch-uuid>.json`. They contain schema
and pipeline versions, run ID, source URL/kind/CIK, nested filing metadata, timestamps,
SHA-256, object URI/byte count, media type, HTTP status, validators, retry count and
processing status. The file omits its own URI; PostgreSQL records include that URI.
Successful acquisitions remain `unprocessed`; Phase 2 never claims parsed data.

PostgreSQL migration `0002_ingestion` provides runs, source work state, append-only
fetches/attempt events and the shared rate clock. Update/delete triggers protect fetch
and attempt history. Filing identity `(CIK, accession)`, document identity (archive URL),
content identity (SHA-256) and fetch identity (UUID) remain separate. Identical bytes
can back several source documents or observations without collapsing provenance.

Filing objects are reusable indefinitely after checksum verification. Mutable JSON
is reusable for `--max-age-hours` (default 24, range 0–8760). `--refresh` revalidates all
selected URLs, including filings, even while fresh. Existing ETag/Last-Modified values
become conditional headers. A 304 requires verified prior bytes and creates a new
fetch observation sharing the object. A changed 200 creates a new immutable version;
neither old bytes nor fetch history are deleted. A 200 omitting validators does not
inherit stale validators. Failed/quarantined acquisitions are never cache hits.

Session-scoped PostgreSQL advisory locks prevent concurrent work on one source and
release on connection loss; busy sources return a recoverable `busy` error. A durable
start event precedes HTTP access. Publication precedes SQL completion, so a crash
cannot commit a success pointing to an incomplete file. Restarting the same command
reclaims interrupted work and verifies completed objects before reusing them. A crash
after publication can leave orphan objects/manifests; rerun can deduplicate the object.

`reconcile` verifies each committed fetch's object bytes, byte count and immutable
manifest, verifies all published object checksums, and reports unreferenced object
counts. It does not delete anything, repair corruption, scan abandoned staging files,
import orphan manifests, or rewrite interrupted run history. Interrupted runs may
remain `running` in historical metadata; subsequent run IDs record recovery separately.
Orphan manifest/staging retention and large-corpus streaming reconciliation are debt.
Missing/corrupt committed bytes block reuse and reconciliation; restore from a trusted
backup or re-acquire into a separate clean store under an explicit recovery procedure.

Downgrade of an empty ingestion schema is tested. Downgrade with any runs or sources
is refused to protect provenance; back up and design an explicit data migration before
rollback. API readiness now requires `0002_ingestion`; API startup still never migrates.

## Scope and acceptance limits

Company Facts validation covers the company identity and JSON envelope; full XBRL
concept/context/financial semantics are deferred to Phase 3. Source lexical numbers,
`fy`, actual period dates and all original bytes remain preserved. No financial
selection, table parsing or calculated results are introduced. HTML is checked for
content type/nonempty bytes, not semantic document correctness.

The automated fixture corpus proves deterministic acquisition, idempotency and
recovery; it is not a live corpus. After the mocked implementation gate, the user
completed a live Apple smoke check: one filing plus submissions and Company Facts,
followed by repeat ingestion without new downloads and two reconciliations reporting
three fetches, three objects and zero orphans. Local bytes were independently checked
against the source manifests. This establishes bounded live acceptance, not broad
live-corpus coverage or financial correctness. Hosted CI, new container builds and production backup durability
are not established by local Python checks. Stop before Phase 3.
