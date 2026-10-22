# WP3.4 Company Facts normalization and selection

Architecture 3.1, ADR-003 and ADR-006. This package reads immutable Bronze bytes;
it does not publish Silver/Gold, change HTML processing, reconcile sources, or
implement tools, formulas, RAG or agents.

## Contracts and versions

`normalize_company_facts(fetch, body)` verifies the existing Bronze checksum,
length, quarantine status and company identity. It returns `NormalizedFacts`
(`xbrl-result-1`) with canonical `Company`, `FinancialFact` and `SourceProvenance`
records, concept labels/descriptions and source occurrences. Pipeline `xbrl-1`,
normalizer `company-facts-1`, period policy `period-boundaries-1`, metric catalog
`reported-metrics-1`, and selector `fact-selection-1` are explicit.

Each occurrence retains a source JSON pointer and compact raw JSON, including
unknown fields and original numeric lexemes. Numbers are parsed as tokens then
Decimal, never float. No scaling, currency conversion, rounding or arithmetic is
applied. Missing optional labels, descriptions, `fy`, `fp` and frame remain missing;
blank labels/descriptions remain blank. Required provenance or invalid dates cause
quarantine of that occurrence without losing its raw source. Unsupported concepts,
units and forms remain available with warnings. Currency is asserted only for USD
and USD/share units; other unit strings are preserved without inferred currency.

Canonical occurrence IDs include the artifact, pointer and processing version;
the existing `FinancialFact.observation_id` separately identifies a logical
reporting. Repeated reportings and duplicate occurrences survive. Source fetch
identity/time remains in provenance, outside logical replay bytes. The envelope
checks ownership, source fields, units, pointers and period diagnostics on read.
Callers must also verify actual bytes/manifests; a valid model alone cannot prove
that an artifact exists or that its contents were faithfully supplied.

Canonical financial rows remain unchanged. The existing `MetricDefinition`
`context_requirement` enum gains `company_facts_entity`; its schema is regenerated.
This additive option preserves existing row identities and the `canonical-1`
encoding. Old readers must update their schema before accepting this new catalog
option. No database migration or dependency change is needed.

## Period and availability semantics

The actual `start` and `end` govern selection, independently of `fy`, `fp`, frame,
form, and filing date. An absent start is an instant; known metric concepts with
an incompatible period kind are rejected. Explicit null/malformed starts are
rejected rather than silently treated as instants. End dates cannot follow filing
availability under the existing canonical fact contract.

Duration classifications remain `unknown` because Company Facts does not establish
the fiscal-year start or the role of every duration. Separate inclusive-day
diagnostics identify quarter-length (75–105), half-year-length (165–200),
nine-month-length (250–290), annual-length (350–380), and other intervals. These
are **length diagnostics**, not verified fiscal quarter/YTD/annual labels. They
cover typical leap and 52/53-week years without deriving dates from fiscal labels.
Exact requested dates distinguish a standalone quarter from YTD and comparatives;
no subtraction derives a quarter, and no annualization is performed.

Selection requires a date cutoff, interpreted as end of that UTC calendar day.
Both filing date and any supplied acceptance timestamp must satisfy it. Company
Facts supplies date-only availability, so no acceptance timestamp is fabricated.
Using a current API snapshot cannot reconstruct missing historical API contents.
Intraday historical selection is outside this interface.

## Catalog and selection policy

Seven reported USD metrics use exactly one `us-gaap` concept each:

- `revenue`: `RevenueFromContractWithCustomerExcludingAssessedTax`.
- `net_income`: `NetIncomeLoss`, attributable to the parent.
- `operating_income`: `OperatingIncomeLoss`.
- `total_assets`: `Assets`.
- `total_liabilities`: `Liabilities`.
- `stockholders_equity`: `StockholdersEquity`, parent permanent equity.
- `operating_cash_flow`: `NetCashProvidedByUsedInOperatingActivities`, including
  discontinued operations.

Aliases are explicit metric names: `assets`, `liabilities`, `net_income_loss`,
and `cash_from_operations`. There is no fuzzy concept-name matching. Broad
`Revenues`, legacy `SalesRevenueNet`, `ProfitLoss`, equity including noncontrolling
interests, and continuing-operations-only cash flow are not silently substituted.
In particular, `revenue` is a narrow customer-contract metric, not a universal
total-revenue measure. Missing mappings return `unsupported`; supported concepts
with no eligible period/unit/form return `unavailable`.

Meanings were inspected against descriptions in the pinned source artifacts. The
[FASB revenue implementation guide](https://xbrl.fasb.org/impdocs/Rev2_TIG/Revenue.htm)
also distinguishes customer-contract revenue from other revenue scopes. These
checks do not establish independent financial selection accuracy or comparability
across companies.

`select_facts(facts, request)` revalidates input contracts, filters exact company,
concept, interval, kind, USD unit/currency, supported form, quality and cutoff,
then applies `original`, `latest_as_of`, or `compare_versions`. It returns the
request, metric identity, versions, selected canonical records, every eligible
alternative, candidate eligibility reasons and warnings. Callers retain the input
dataset to resolve rejected candidate IDs; the corpus report pins the input hashes.

Equivalent occurrences within an accession collapse only for selection; every
source link remains in alternatives. Conflicting logical observations within any
eligible accession cause abstention. Original/latest selects the earliest/latest
eligible filing date for the **exact period**; equal-day incompatible amounts cause
ambiguity. Equivalent ties use accession then canonical fact ID, never input order.
`compare_versions` returns one representative per accession, preserving changing
amounts without declaring that a restatement occurred.

The [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
limits these APIs to non-custom taxonomy facts applying to the filing entity.
The default `company_facts_entity` policy permits that bounded reported-source
scope, with an explicit warning. Context IDs and dimensions remain unknown; no
empty dimension set is invented. `verified_consolidated` requests abstain on these
unknown contexts. Verified nonempty dimensions are always ineligible. Neither
policy establishes subsidiary, segment, or all-extension coverage.

## Quality and operation

The established states are retained: `passed` for completed integrity diagnostics,
`warning` for retained Company Facts observations/selected source-scoped results,
and `failed` for rejected occurrences. All normalized Company Facts facts carry
the unknown-context warning; normalization is not a semantic pass. Failure reasons
are structured codes. Artifact-level malformed JSON, duplicate keys, wrong CIK,
bad structure or checksum errors raise `XbrlError` with a safe code; Bronze remains
unchanged. The parser limits an artifact to 32 MiB and 250,000 occurrences, but this
is not a measured worst-case resource guarantee.

Run offline from the repository root:

```bash
bash scripts/uv.sh run --frozen python -m sec_research.processing.xbrl_corpus \
  --as-of 2026-10-21 \
  --examples tests/fixtures/xbrl/reported-examples.json \
  --output .runtime/wp34/diagnostics.json
```

The command audits existing objects/manifests before and after processing, checks
exact replay and serialization, resolves every observation/concept pointer, checks
the 15 source-linked examples, and writes five envelopes plus a small report.
The output is diagnostic JSON, not a physical Silver/Gold publication. Large
outputs remain ignored. The report records source/code/lock/input hashes and
seven annual selection probes per company. Those probes use a source-derived
annual net-income interval; they are diagnostics, not independent expected labels.

See the [package review](phase-3-wp3.4-review.md) for measured results. WP3.3
financial adjudication was deferred by the owner; WP33-REV-001 through -006 and
the JPMorgan section-classification limitations remain unresolved. HTML evidence
is retained separately and never overwrites these facts. WP3.5 remains a separate,
explicitly authorized gate.
