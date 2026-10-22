"""Preserve Company Facts JSON versions; financial normalization belongs to Phase 3."""

from sec_research.contracts.sec import Source, normalize_cik
from sec_research.ingestion.acquisition import Acquisition


def ingest_company_facts(acquisition: Acquisition, cik: str) -> bytes:
    cik = normalize_cik(cik)
    return acquisition.get(
        Source(
            kind="company_facts",
            cik=cik,
            url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
        )
    )
