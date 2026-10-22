"""Validate acquisition envelopes without interpreting XBRL or parsing documents."""

import json
import re
from datetime import date
from decimal import Decimal
from typing import cast

from pydantic import ValidationError

from sec_research.contracts.sec import (
    Filing,
    IngestionCode,
    IngestionError,
    Source,
    normalize_accession,
    normalize_cik,
)


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise ValueError("nonfinite JSON number")


def json_object(body: bytes) -> dict[str, object]:
    try:
        result: object = json.loads(
            body, object_pairs_hook=_unique, parse_float=Decimal, parse_constant=_nonfinite
        )
    except (ValueError, UnicodeError, RecursionError):
        raise IngestionError(IngestionCode.INVALID_METADATA) from None
    if not isinstance(result, dict):
        raise IngestionError(IngestionCode.INVALID_METADATA)
    return cast(dict[str, object], result)


def object_field(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise IngestionError(IngestionCode.INVALID_METADATA)
    return cast(dict[str, object], value)


def array_field(value: object) -> list[object]:
    if not isinstance(value, list):
        raise IngestionError(IngestionCode.INVALID_METADATA)
    return cast(list[object], value)


def text_field(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise IngestionError(IngestionCode.INVALID_METADATA)
    return value


def validate_payload(source: Source, body: bytes, media_type: str) -> None:
    if source.kind == "filing":
        if media_type not in {"text/html", "application/xhtml+xml"} or not body.strip():
            raise IngestionError(IngestionCode.INVALID_METADATA)
        return
    if media_type not in {"application/json", "text/json"}:
        raise IngestionError(IngestionCode.INVALID_METADATA)
    data = json_object(body)
    if source.kind in {"submissions", "company_facts"}:
        cik = data.get("cik")
        if not isinstance(cik, (str, int)) or normalize_cik(cik) != source.cik:
            raise IngestionError(IngestionCode.INVALID_METADATA)
    if source.kind == "submissions":
        text_field(data.get("name"))
        filings = object_field(data.get("filings"))
        filing_rows(object_field(filings.get("recent")), source.cik or "")
        historical_files(filings, source.cik or "")
    elif source.kind == "history":
        filing_rows(data, source.cik or "")
    elif source.kind == "company_facts":
        text_field(data.get("entityName"))
        object_field(data.get("facts"))
    elif source.kind == "companies":
        for value in data.values():
            company = object_field(value)
            cik = company.get("cik_str")
            if not isinstance(cik, (str, int)):
                raise IngestionError(IngestionCode.INVALID_METADATA)
            normalize_cik(cik)
            text_field(company.get("ticker"))
            text_field(company.get("title"))


def validate_columns(data: dict[str, object]) -> dict[str, list[object]]:
    columns = {
        key: array_field(data.get(key))
        for key in ("accessionNumber", "filingDate", "form", "primaryDocument")
    }
    count = len(columns["accessionNumber"])
    for key in ("reportDate", "acceptanceDateTime"):
        if key in data:
            columns[key] = array_field(data[key])
    if any(len(values) != count for values in columns.values()):
        raise IngestionError(IngestionCode.INVALID_METADATA)
    if any(not isinstance(value, str) for values in columns.values() for value in values):
        raise IngestionError(IngestionCode.INVALID_METADATA)
    return columns


def iso_date(value: object) -> date:
    text = text_field(value)
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text):
        raise IngestionError(IngestionCode.INVALID_METADATA)
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise IngestionError(IngestionCode.INVALID_METADATA) from None


def filing_rows(data: dict[str, object], cik: str) -> list[Filing]:
    columns = validate_columns(data)
    result: list[Filing] = []
    for index, form in enumerate(columns["form"]):
        accession = normalize_accession(text_field(columns["accessionNumber"][index]))
        filed = iso_date(columns["filingDate"][index])
        if form not in {"10-K", "10-Q", "10-K/A", "10-Q/A"}:
            continue
        values: dict[str, object] = {
            "cik": cik,
            "accession": accession,
            "form": form,
            "filing_date": filed,
            "primary_document": columns["primaryDocument"][index],
        }
        if "reportDate" in columns and columns["reportDate"][index]:
            values["report_date"] = iso_date(columns["reportDate"][index])
        if "acceptanceDateTime" in columns and columns["acceptanceDateTime"][index]:
            accepted = text_field(columns["acceptanceDateTime"][index])
            # Only preserve an explicitly zoned source timestamp; never fabricate UTC.
            if not re.search(r"(?:Z|[+-][0-9]{2}:[0-9]{2})$", accepted):
                raise IngestionError(IngestionCode.INVALID_METADATA)
            values["accepted_at"] = accepted
        try:
            result.append(Filing.model_validate(values))
        except ValidationError:
            raise IngestionError(IngestionCode.INVALID_METADATA) from None
    return result


def historical_files(filings: dict[str, object], cik: str) -> list[tuple[Source, date, date]]:
    result: list[tuple[Source, date, date]] = []
    for raw in array_field(filings.get("files")):
        descriptor = object_field(raw)
        name = text_field(descriptor.get("name"))
        first, last = iso_date(descriptor.get("filingFrom")), iso_date(descriptor.get("filingTo"))
        count = descriptor.get("filingCount")
        if first > last or isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise IngestionError(IngestionCode.INVALID_METADATA)
        try:
            source = Source(kind="history", cik=cik, url=f"https://data.sec.gov/submissions/{name}")
        except ValidationError:
            raise IngestionError(IngestionCode.INVALID_METADATA) from None
        result.append((source, first, last))
    return result
