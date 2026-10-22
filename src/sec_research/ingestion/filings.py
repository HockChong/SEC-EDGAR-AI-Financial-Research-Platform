"""Discover recent and historical 10-K/Q accessions without inferring reporting periods."""

from datetime import date

from sec_research.contracts.sec import Filing, IngestionCode, IngestionError, Source, normalize_cik
from sec_research.ingestion.acquisition import Acquisition
from sec_research.ingestion.payloads import (
    filing_rows,
    historical_files,
    json_object,
    object_field,
)


def discover_filings(
    acquisition: Acquisition,
    cik: str,
    *,
    start: date | None = None,
    end: date | None = None,
    include_amendments: bool = False,
    max_filings: int = 20,
    max_history_files: int = 100,
) -> list[Filing]:
    cik = normalize_cik(cik)
    if max_filings < 1 or max_history_files < 1 or (start and end and start > end):
        raise IngestionError(IngestionCode.INVALID_METADATA)
    root = json_object(
        acquisition.get(
            Source(
                kind="submissions", cik=cik, url=f"https://data.sec.gov/submissions/CIK{cik}.json"
            )
        )
    )
    filing_data = object_field(root.get("filings"))
    blocks = [object_field(filing_data.get("recent"))]
    history_sources: dict[str, Source] = {}
    for source, first, last in historical_files(filing_data, cik):
        if (start and last < start) or (end and first > end):
            continue
        history_sources[source.url] = source
    if len(history_sources) > max_history_files:
        raise IngestionError(IngestionCode.INVALID_METADATA)
    for source in sorted(history_sources.values(), key=lambda item: item.url):
        blocks.append(json_object(acquisition.get(source)))
    found: dict[str, Filing] = {}
    forms = {"10-K", "10-Q", "10-K/A", "10-Q/A"} if include_amendments else {"10-K", "10-Q"}
    for block in blocks:
        for filing in filing_rows(block, cik):
            if filing.form not in forms:
                continue
            previous = found.get(filing.accession)
            if previous is not None and previous != filing:
                raise IngestionError(IngestionCode.INVALID_METADATA)
            found[filing.accession] = filing
    filtered = [
        filing
        for filing in found.values()
        if (start is None or filing.filing_date >= start)
        and (end is None or filing.filing_date <= end)
    ]
    return sorted(filtered, key=lambda item: (item.filing_date, item.accession), reverse=True)[
        :max_filings
    ]
