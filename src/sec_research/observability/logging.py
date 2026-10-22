"""Allowlisted JSON logging: arbitrary messages, extras and exceptions are never emitted."""

import json
import logging
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from sec_research.contracts.errors import ErrorCode


class Event(StrEnum):
    SEC_RESPONSE = "sec_response"
    SEC_RETRY = "sec_retry"
    INGESTION_SUCCEEDED = "ingestion_succeeded"
    INGESTION_FAILED = "ingestion_failed"
    REQUEST_COMPLETED = "request_completed"
    REQUEST_FAILED = "request_failed"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event = getattr(record, "event", None)
        payload: dict[str, str | int | float] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "severity": logging.getLevelName(record.levelno),
            "event": event.value if isinstance(event, Event) else "unstructured_log",
        }
        request_id = getattr(record, "request_id", None)
        if isinstance(request_id, UUID):
            payload["request_id"] = str(request_id)
        error_code = getattr(record, "error_code", None)
        if isinstance(error_code, ErrorCode):
            payload["error_code"] = error_code.value
        duration = getattr(record, "duration_ms", None)
        if isinstance(duration, (float, int)) and 0 <= duration < float("inf"):
            payload["duration_ms"] = round(duration, 3)
        status = getattr(record, "status_code", None)
        if isinstance(status, int) and 100 <= status <= 599:
            payload["status_code"] = status
        return json.dumps(payload, allow_nan=False)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    # Uvicorn's default access/error handlers would bypass the safe formatter.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
