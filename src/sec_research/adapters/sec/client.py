"""Bounded identifying SEC access. Redirects and ambient proxies are disabled."""

import logging
import random
import re
import ssl
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from http.client import HTTPException, HTTPSConnection
from typing import Protocol
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sec_research.contracts.sec import IngestionCode, IngestionError, validate_sec_url
from sec_research.observability.logging import Event

logger = logging.getLogger(__name__)


class SecPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    user_agent: str = Field(min_length=8, max_length=256, repr=False)
    requests_per_second: float = Field(default=5, gt=0, le=5, allow_inf_nan=False)
    timeout: float = Field(default=15, gt=0, le=60, allow_inf_nan=False)
    deadline: float = Field(default=120, gt=0, le=600, allow_inf_nan=False)
    max_attempts: int = Field(default=4, ge=1, le=8)
    max_bytes: int = Field(default=32 * 1024 * 1024, ge=1, le=128 * 1024 * 1024)

    @field_validator("user_agent")
    @classmethod
    def identifying(cls, value: str) -> str:
        if any(ord(char) < 32 or ord(char) > 126 for char in value) or not re.search(
            r"\S+\s+.*[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value
        ):
            raise ValueError("SEC User-Agent requires organization and contact email")
        return value


@dataclass(frozen=True)
class Response:
    status: int
    body: bytes
    headers: Mapping[str, str]
    attempts: int = 1


class Transport(Protocol):
    def __call__(
        self, url: str, headers: Mapping[str, str], timeout: float, max_bytes: int
    ) -> Response: ...


class Limiter(Protocol):
    def wait(self, deadline: float) -> None: ...


class LocalLimiter:
    """Shared across clients in one process; CLI uses the PostgreSQL limiter instead."""

    def __init__(
        self,
        rate: float = 5,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not 0 < rate <= 5:
            raise ValueError("rate must be greater than zero and at most five")
        self.interval = 1 / rate
        self.clock = clock
        self.sleep = sleep
        self.next_request = 0.0
        self.lock = threading.Lock()

    def wait(self, deadline: float) -> None:
        with self.lock:
            delay = max(0.0, self.next_request - self.clock())
            if self.clock() + delay >= deadline:
                raise IngestionError(IngestionCode.DEADLINE, retryable=True)
            self.sleep(delay)
            self.next_request = self.clock() + self.interval


_shared_limiter = LocalLimiter()


def https_transport(
    url: str, headers: Mapping[str, str], timeout: float, max_bytes: int
) -> Response:
    validate_sec_url(url)
    parsed = urlsplit(url)
    finish = time.monotonic() + timeout
    connection = HTTPSConnection(
        parsed.netloc, timeout=timeout, context=ssl.create_default_context()
    )
    try:
        connection.connect()
        socket = connection.sock
        if socket is None:
            raise IngestionError(IngestionCode.NETWORK_FAILURE, retryable=True)

        def remaining() -> None:
            budget = finish - time.monotonic()
            if budget <= 0:
                raise IngestionError(IngestionCode.DEADLINE, retryable=True)
            socket.settimeout(budget)

        remaining()
        connection.request("GET", parsed.path, headers=dict(headers))
        remaining()
        with connection.getresponse() as opened:
            response_headers = {k.lower(): v for k, v in opened.getheaders()}
            # No redirects are followed; do not read error-page bodies.
            if opened.status != 200:
                return Response(opened.status, b"", response_headers)
            if response_headers.get("content-encoding", "identity").lower() != "identity":
                raise IngestionError(IngestionCode.INVALID_METADATA)
            chunks: list[bytes] = []
            size = 0
            while True:
                remaining()
                chunk = opened.read1(min(65536, max_bytes + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                if size > max_bytes:
                    raise IngestionError(IngestionCode.TOO_LARGE)
            length = response_headers.get("content-length")
            if length is not None and (not length.isdecimal() or int(length) != size):
                raise IngestionError(IngestionCode.INTEGRITY, retryable=True)
            return Response(opened.status, b"".join(chunks), response_headers)
    finally:
        connection.close()


class SecClient:
    def __init__(
        self,
        policy: SecPolicy,
        *,
        transport: Transport = https_transport,
        limiter: Limiter | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        jitter: Callable[[], float] = random.random,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.policy = policy
        self.transport = transport
        if limiter is None and policy.requests_per_second != 5:
            raise ValueError("custom rate requires a shared limiter configured at that rate")
        self.limiter = limiter if limiter is not None else _shared_limiter
        self.clock, self.sleep, self.jitter, self.now = clock, sleep, jitter, now

    def get(self, url: str, validators: Mapping[str, str] | None = None) -> Response:
        validate_sec_url(url)
        headers = {"User-Agent": self.policy.user_agent, "Accept-Encoding": "identity"}
        for key, value in (validators or {}).items():
            if key not in {"If-None-Match", "If-Modified-Since"} or "\r" in value or "\n" in value:
                raise IngestionError(IngestionCode.INVALID_METADATA)
            headers[key] = value
        deadline = self.clock() + self.policy.deadline
        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                self.limiter.wait(deadline)
            except IngestionError as error:
                error.attempts = attempt - 1
                raise
            remaining = deadline - self.clock()
            if remaining <= 0:
                raise IngestionError(IngestionCode.DEADLINE, retryable=True, attempts=attempt - 1)
            retry_after = 0.0
            try:
                response = self.transport(
                    url, headers, min(remaining, self.policy.timeout), self.policy.max_bytes
                )
                if self.clock() >= deadline:
                    raise IngestionError(IngestionCode.DEADLINE, retryable=True)
                if len(response.body) > self.policy.max_bytes:
                    raise IngestionError(IngestionCode.TOO_LARGE)
                status = response.status
                logger.info(
                    "SEC response", extra={"event": Event.SEC_RESPONSE, "status_code": status}
                )
                if status in {200, 304}:
                    return Response(status, response.body, response.headers, attempt)
                if status == 403:
                    raise IngestionError(IngestionCode.ACCESS_DENIED)
                if status == 429:
                    code = IngestionCode.RATE_LIMITED
                elif status in {500, 502, 503, 504}:
                    code = IngestionCode.HTTP_FAILURE
                else:
                    raise IngestionError(IngestionCode.HTTP_FAILURE)
                raw = response.headers.get("retry-after", "")
                try:
                    retry_after = max(0.0, float(int(raw)))
                except (ValueError, OverflowError):
                    try:
                        retry_after = max(
                            0.0, (parsedate_to_datetime(raw) - self.now()).total_seconds()
                        )
                    except (ValueError, TypeError, OverflowError):
                        retry_after = 0.0
            except (HTTPException, OSError):
                code = IngestionCode.NETWORK_FAILURE
            except IngestionError as error:
                error.attempts = attempt
                if not error.retryable:
                    raise
                code = error.code
            if attempt == self.policy.max_attempts:
                raise IngestionError(code, retryable=True, attempts=attempt)
            delay = max(retry_after, min(30.0, 2.0 ** (attempt - 1)) * (0.5 + self.jitter()))
            if self.clock() + delay >= deadline:
                raise IngestionError(IngestionCode.DEADLINE, retryable=True, attempts=attempt)
            logger.info("SEC retry", extra={"event": Event.SEC_RETRY})
            self.sleep(delay)
        raise AssertionError("validated attempt budget cannot be empty")
