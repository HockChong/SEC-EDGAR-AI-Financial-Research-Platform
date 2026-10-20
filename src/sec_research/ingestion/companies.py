"""Exact company alias lookup through the official SEC ticker catalog."""

from sec_research.contracts.sec import IngestionCode, IngestionError, Source, normalize_cik
from sec_research.ingestion.acquisition import Acquisition
from sec_research.ingestion.payloads import json_object, object_field, text_field


def resolve_company(query: str, acquisition: Acquisition) -> str:
    if query.isascii() and query.isdigit():
        return normalize_cik(query)
    source = Source(url="https://www.sec.gov/files/company_tickers.json", kind="companies")
    catalog = json_object(acquisition.get(source))
    matches: set[str] = set()
    for raw in catalog.values():
        company = object_field(raw)
        ticker, name = text_field(company.get("ticker")), text_field(company.get("title"))
        cik = company.get("cik_str")
        if not isinstance(cik, (str, int)):
            raise IngestionError(IngestionCode.INVALID_METADATA)
        if query.casefold() in {ticker.casefold(), name.casefold()}:
            matches.add(normalize_cik(cik))
    if len(matches) != 1:
        raise IngestionError(IngestionCode.INVALID_METADATA)
    return matches.pop()
