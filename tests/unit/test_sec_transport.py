"""Exercise the real transport against mocked HTTPS connections, never live hosts."""

from unittest.mock import MagicMock

import pytest

from sec_research.adapters.sec.client import https_transport
from sec_research.contracts.sec import IngestionError

URL = "https://data.sec.gov/submissions/CIK0000000001.json"


def connection(
    monkeypatch: pytest.MonkeyPatch,
    body: bytes,
    *,
    status: int = 200,
    headers: list[tuple[str, str]] | None = None,
) -> tuple[MagicMock, MagicMock]:
    result = MagicMock()
    response = result.getresponse.return_value.__enter__.return_value
    response.status = status
    response.getheaders.return_value = headers or [("Content-Length", str(len(body)))]
    response.read1.side_effect = [body, b""]
    constructor = MagicMock(return_value=result)
    monkeypatch.setattr("sec_research.adapters.sec.client.HTTPSConnection", constructor)
    return result, constructor


def test_https_verified_context_path_headers_and_exact_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    conn, constructor = connection(monkeypatch, b"  original\n")
    result = https_transport(URL, {"User-Agent": "Synthetic"}, 2, 100)
    assert result.body == b"  original\n"
    assert constructor.call_args.kwargs["context"].check_hostname
    conn.request.assert_called_once_with(
        "GET", "/submissions/CIK0000000001.json", headers={"User-Agent": "Synthetic"}
    )
    assert conn.sock.settimeout.call_count >= 3
    conn.close.assert_called_once()


@pytest.mark.parametrize(
    "headers,code",
    [
        ([("Content-Length", "100")], "integrity"),
        ([("Content-Length", "invalid")], "integrity"),
        ([("Content-Encoding", "gzip")], "invalid_metadata"),
    ],
)
def test_truncation_and_compression_rejected(
    monkeypatch: pytest.MonkeyPatch, headers: list[tuple[str, str]], code: str
) -> None:
    conn, _ = connection(monkeypatch, b"short", headers=headers)
    with pytest.raises(IngestionError, match=code):
        https_transport(URL, {}, 2, 100)
    conn.close.assert_called_once()


def test_limit_redirect_and_socket_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    conn, _ = connection(monkeypatch, b"123")
    with pytest.raises(IngestionError, match="too_large"):
        https_transport(URL, {}, 2, 2)
    conn, _ = connection(monkeypatch, b"private", status=302)
    assert https_transport(URL, {}, 2, 100).status == 302
    conn.getresponse.return_value.__enter__.return_value.read1.assert_not_called()
    conn, _ = connection(monkeypatch, b"")
    conn.sock = None
    with pytest.raises(IngestionError, match="network_failure"):
        https_transport(URL, {}, 2, 100)


def test_total_attempt_deadline_includes_connect_time(monkeypatch: pytest.MonkeyPatch) -> None:
    conn, _ = connection(monkeypatch, b"body")
    monkeypatch.setattr(
        "sec_research.adapters.sec.client.time.monotonic", MagicMock(side_effect=[0, 3])
    )
    with pytest.raises(IngestionError, match="deadline"):
        https_transport(URL, {}, 2, 100)
    conn.close.assert_called_once()
