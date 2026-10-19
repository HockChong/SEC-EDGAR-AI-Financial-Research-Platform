"""Stable error codes; messages never contain underlying exception text."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ErrorCode(StrEnum):
    DATABASE_UNAVAILABLE = "database_unavailable"
    SCHEMA_NOT_READY = "schema_not_ready"
    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"
    HTTP_ERROR = "http_error"
    INTERNAL_ERROR = "internal_error"


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: ErrorCode
    message: str
    retryable: bool
    request_id: UUID
