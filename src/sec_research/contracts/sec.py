"""Version 1 ingestion contracts; raw SEC bytes remain authoritative."""

import re
from datetime import date, datetime
from enum import StrEnum
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class IngestionCode(StrEnum):
    INVALID_METADATA = "invalid_metadata"
    ACCESS_DENIED = "access_denied"
    RATE_LIMITED = "rate_limited"
    HTTP_FAILURE = "http_failure"
    NETWORK_FAILURE = "network_failure"
    DEADLINE = "deadline"
    TOO_LARGE = "too_large"
    UNSAFE_URL = "unsafe_url"
    INTEGRITY = "integrity"
    STORAGE = "storage"
    BUSY = "busy"


class IngestionError(Exception):
    def __init__(self, code: IngestionCode, *, retryable: bool = False, attempts: int = 0) -> None:
        self.code = code
        self.retryable = retryable
        self.attempts = attempts
        super().__init__(code.value)


def normalize_cik(value: str | int) -> str:
    text = str(value)
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]{1,10}", text) or int(text) == 0:
        raise IngestionError(IngestionCode.INVALID_METADATA)
    return text.zfill(10)


def normalize_accession(value: str) -> str:
    if re.fullmatch(r"[0-9]{18}", value):
        return f"{value[:10]}-{value[10:12]}-{value[12:]}"
    if not re.fullmatch(r"[0-9]{10}-[0-9]{2}-[0-9]{6}", value):
        raise IngestionError(IngestionCode.INVALID_METADATA)
    return value


def validate_sec_url(value: str) -> str:
    parsed = urlsplit(value)
    valid = (
        parsed.scheme == "https"
        and parsed.netloc in {"data.sec.gov", "www.sec.gov"}
        and not parsed.query
        and not parsed.fragment
        and (
            (
                parsed.netloc == "data.sec.gov"
                and re.fullmatch(
                    r"/(submissions/CIK[0-9]{10}(?:-submissions-[0-9]+)?\.json"
                    r"|api/xbrl/companyfacts/CIK[0-9]{10}\.json)",
                    parsed.path,
                )
            )
            or (
                parsed.netloc == "www.sec.gov"
                and re.fullmatch(
                    r"/Archives/edgar/data/[0-9]+/[0-9]{18}/[A-Za-z0-9_-][A-Za-z0-9_.-]*",
                    parsed.path,
                )
            )
            or (parsed.netloc == "www.sec.gov" and parsed.path == "/files/company_tickers.json")
        )
    )
    if not valid:
        raise IngestionError(IngestionCode.UNSAFE_URL)
    return value


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    schema_version: Literal["1"] = "1"


class Filing(Contract):
    cik: str
    accession: str
    form: Literal["10-K", "10-Q", "10-K/A", "10-Q/A"]
    filing_date: date
    report_date: date | None = None
    accepted_at: datetime | None = None
    primary_document: str = Field(pattern=r"^[A-Za-z0-9_-][A-Za-z0-9_.-]*\.(?:htm|html)$")

    @field_validator("cik")
    @classmethod
    def cik_valid(cls, value: str) -> str:
        return normalize_cik(value)

    @field_validator("accession")
    @classmethod
    def accession_valid(cls, value: str) -> str:
        return normalize_accession(value)

    @property
    def source_url(self) -> str:
        return (
            f"https://www.sec.gov/Archives/edgar/data/{int(self.cik)}/"
            f"{self.accession.replace('-', '')}/{self.primary_document}"
        )


class Source(Contract):
    url: str
    kind: Literal["submissions", "history", "filing", "company_facts", "companies"]
    cik: str | None = None
    filing: Filing | None = None

    @field_validator("url")
    @classmethod
    def url_valid(cls, value: str) -> str:
        return validate_sec_url(value)

    @field_validator("cik")
    @classmethod
    def cik_valid(cls, value: str | None) -> str | None:
        return normalize_cik(value) if value is not None else None

    @model_validator(mode="after")
    def identity_valid(self) -> "Source":
        expected: str
        match self.kind:
            case "companies":
                expected = "https://www.sec.gov/files/company_tickers.json"
                valid = self.cik is None and self.filing is None and self.url == expected
            case "filing":
                valid = (
                    self.filing is not None
                    and self.cik == self.filing.cik
                    and self.url == self.filing.source_url
                )
            case "submissions":
                expected = f"https://data.sec.gov/submissions/CIK{self.cik}.json"
                valid = self.cik is not None and self.filing is None and self.url == expected
            case "company_facts":
                expected = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{self.cik}.json"
                valid = self.cik is not None and self.filing is None and self.url == expected
            case "history":
                valid = (
                    self.cik is not None
                    and self.filing is None
                    and bool(
                        re.fullmatch(
                            rf"https://data\.sec\.gov/submissions/CIK{self.cik}-submissions-[0-9]+\.json",
                            self.url,
                        )
                    )
                )
        if not valid:
            raise ValueError("source identity mismatch")
        return self
