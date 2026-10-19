import json
import logging
import sys
from uuid import uuid4

import pytest

from sec_research.contracts.errors import ErrorCode
from sec_research.observability.logging import Event, JsonFormatter, configure_logging


def test_structured_event_retains_safe_correlation_metadata() -> None:
    request_id = uuid4()
    record = logging.makeLogRecord(
        {
            "levelno": logging.INFO,
            "event": Event.REQUEST_FAILED,
            "request_id": request_id,
            "error_code": ErrorCode.DATABASE_UNAVAILABLE,
            "duration_ms": 12.3456,
            "status_code": 503,
        }
    )
    payload = json.loads(JsonFormatter().format(record))
    assert payload["request_id"] == str(request_id)
    assert payload["event"] == "request_failed"
    assert payload["error_code"] == "database_unavailable"
    assert payload["status_code"] == 503
    assert payload["duration_ms"] == 12.346
    assert payload["timestamp"].endswith("+00:00")


def test_untrusted_messages_exceptions_and_nested_extras_are_not_logged() -> None:
    try:
        raise ValueError("secret-password in exception")
    except ValueError:
        record = logging.makeLogRecord(
            {
                "levelno": logging.ERROR,
                "msg": "secret-password %s",
                "args": ("private token",),
                "exc_info": sys.exc_info(),
                "stack_info": "private stack",
                "event": "secret-password",
                "request_id": "private token",
                "error_code": "private token",
                "nested": {"authorization": "private token"},
            }
        )
    encoded = JsonFormatter().format(record)
    assert "secret-password" not in encoded
    assert "private" not in encoded
    assert json.loads(encoded)["event"] == "unstructured_log"


@pytest.mark.parametrize("duration", [float("nan"), float("inf"), -1, "private"])
def test_invalid_durations_do_not_break_json(duration: object) -> None:
    record = logging.makeLogRecord({"levelno": logging.INFO, "duration_ms": duration})
    assert "duration_ms" not in json.loads(JsonFormatter().format(record))


def test_logging_configuration_is_repeatable_and_covers_uvicorn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = logging.getLogger()
    monkeypatch.setattr(root, "handlers", [])
    monkeypatch.setattr(root, "level", logging.WARNING)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        monkeypatch.setattr(logger, "handlers", [logging.NullHandler()])
        monkeypatch.setattr(logger, "propagate", False)
    configure_logging("INFO")
    configure_logging("INFO")
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        assert not logger.handlers
        assert logger.propagate
