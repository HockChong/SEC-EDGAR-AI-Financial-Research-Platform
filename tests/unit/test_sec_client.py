"""Synthetic SEC responses only; no live SEC request is made."""

from http.client import RemoteDisconnected

import pytest
from pydantic import ValidationError

from sec_research.adapters.sec.client import LocalLimiter, Response, SecClient, SecPolicy
from sec_research.contracts.sec import (
    IngestionCode,
    IngestionError,
    normalize_accession,
    normalize_cik,
)
from tests.sec_helpers import Clock, FakeTransport, client

URL = "https://data.sec.gov/submissions/CIK0000000001.json"


def test_identity_and_original_response_bytes() -> None:
    transport = FakeTransport(Response(200, b'{ "x": 1 }\n', {}))
    assert client(transport, Clock()).get(URL).body == b'{ "x": 1 }\n'
    assert transport.requests[0][1] == {
        "User-Agent": "SyntheticTests contact@example.test",
        "Accept-Encoding": "identity",
    }


@pytest.mark.parametrize("identity", ["", "anonymous", "contact@example.test", "Org\r\nx a@b.com"])
def test_invalid_identity_rejected(identity: str) -> None:
    with pytest.raises(ValidationError):
        SecPolicy(user_agent=identity)


def test_shared_limiter_coordinates_clients_and_honors_deadline() -> None:
    clock = Clock()
    limiter = LocalLimiter(clock=clock.now, sleep=clock.sleep)
    policy = SecPolicy(user_agent="Synthetic contact@example.test")
    transport = FakeTransport(*(Response(200, b"{}", {}) for _ in range(3)))
    first = SecClient(policy, transport=transport, limiter=limiter, clock=clock.now)
    second = SecClient(policy, transport=transport, limiter=limiter, clock=clock.now)
    first.get(URL)
    second.get(URL)
    assert clock.value == pytest.approx(0.2)
    with pytest.raises(IngestionError, match="deadline"):
        limiter.wait(0.3)


@pytest.mark.parametrize("failure", [429, 500, 502, 503, 504, "network"])
def test_transient_retries_backoff_and_counts(failure: int | str) -> None:
    response = (
        RemoteDisconnected("private connection details")
        if failure == "network"
        else Response(int(failure), b"", {})
    )
    transport = FakeTransport(response, response, Response(200, b"{}", {}))
    clock = Clock()
    assert client(transport, clock).get(URL).attempts == 3
    assert clock.value == pytest.approx(1.5)
    assert len(transport.requests) == 3


@pytest.mark.parametrize("retry_after", ["5", "Thu, 01 Jan 2026 00:00:05 GMT"])
def test_retry_after_seconds_and_http_date(retry_after: str) -> None:
    clock = Clock()
    transport = FakeTransport(
        Response(429, b"", {"retry-after": retry_after}), Response(200, b"{}", {})
    )
    client(transport, clock).get(URL)
    assert clock.value == 5


@pytest.mark.parametrize("status", [301, 302, 307, 403, 404, 501])
def test_permanent_failures_and_redirects_are_not_retried(status: int) -> None:
    transport = FakeTransport(
        Response(status, b"private response", {"location": "https://evil.test"})
    )
    with pytest.raises(IngestionError) as caught:
        client(transport, Clock()).get(URL)
    assert not caught.value.retryable
    assert caught.value.attempts == 1
    assert len(transport.requests) == 1
    assert "private" not in str(caught.value)


def test_budget_exhaustion_and_retry_after_exceeding_deadline() -> None:
    transport = FakeTransport(*(Response(503, b"", {}) for _ in range(4)))
    with pytest.raises(IngestionError) as caught:
        client(transport, Clock()).get(URL)
    assert caught.value.attempts == 4
    assert caught.value.retryable
    transport = FakeTransport(Response(429, b"", {"retry-after": "1000"}))
    with pytest.raises(IngestionError, match="deadline"):
        client(transport, Clock(), deadline=3).get(URL)


def test_limits_and_unsafe_request_metadata() -> None:
    transport = FakeTransport(Response(200, b"123", {}))
    with pytest.raises(IngestionError, match="too_large"):
        client(transport, Clock(), max_bytes=2).get(URL)
    for url in [
        "http://data.sec.gov/submissions/CIK0000000001.json",
        "https://evil.test/",
        "https://data.sec.gov:443/submissions/CIK0000000001.json",
        URL + "?token=private",
        "https://www.sec.gov/Archives/../private",
    ]:
        with pytest.raises(IngestionError, match="unsafe_url"):
            client(FakeTransport(), Clock()).get(url)
    with pytest.raises(IngestionError, match="invalid_metadata"):
        client(FakeTransport(), Clock()).get(URL, {"Authorization": "private"})


@pytest.mark.parametrize("value", [0, True, -1, "12345678901", " 1", "1.0", "\u0661"])
def test_bad_cik(value: str | int) -> None:
    with pytest.raises(IngestionError):
        normalize_cik(value)


def test_cik_and_accession_canonicalization() -> None:
    assert normalize_cik(1) == "0000000001"
    assert normalize_cik("0000000001") == "0000000001"
    assert normalize_accession("000000000126000001") == "0000000001-26-000001"
    assert normalize_accession("0000000001-26-000001") == "0000000001-26-000001"
    with pytest.raises(IngestionError):
        normalize_accession("../../private")


def test_json_304_and_invalid_retry_header() -> None:
    transport = FakeTransport(
        Response(503, b"", {"retry-after": "invalid"}), Response(304, b"", {})
    )
    assert client(transport, Clock()).get(URL, {"If-None-Match": '"v1"'}).status == 304
    assert transport.requests[0][1]["If-None-Match"] == '"v1"'
    assert IngestionCode.HTTP_FAILURE.value == "http_failure"
