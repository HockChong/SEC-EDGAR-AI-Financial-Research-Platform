"""Boundary validation for the public error envelope."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from sec_research.contracts.errors import ErrorCode, ErrorResponse


def test_error_round_trips_through_json() -> None:
    error = ErrorResponse(
        code=ErrorCode.DATABASE_UNAVAILABLE,
        message="Database is unavailable.",
        retryable=True,
        request_id=uuid4(),
    )
    assert ErrorResponse.model_validate_json(error.model_dump_json()) == error


@pytest.mark.parametrize(
    "overrides",
    [{"code": "unknown"}, {"request_id": "bad-id"}, {"traceback": "private details"}],
)
def test_error_rejects_invalid_boundary_data(overrides: dict[str, object]) -> None:
    payload: dict[str, object] = {
        "code": "internal_error",
        "message": "Request failed.",
        "retryable": False,
        "request_id": str(uuid4()),
    }
    payload.update(overrides)
    with pytest.raises(ValidationError):
        ErrorResponse.model_validate(payload)
