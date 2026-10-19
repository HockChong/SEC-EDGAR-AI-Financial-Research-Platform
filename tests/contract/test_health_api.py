from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from starlette.exceptions import HTTPException

from sec_research.api.app import create_app
from sec_research.contracts.errors import ErrorCode, ErrorResponse
from sec_research.settings import Settings


class FakeDatabase:
    def __init__(self, error: ErrorCode | None = None) -> None:
        self.error = error
        self.calls = 0
        self.closed = False

    def readiness(self) -> ErrorCode | None:
        self.calls += 1
        return self.error

    def close(self) -> None:
        self.closed = True


def config() -> Settings:
    return Settings(database_url=SecretStr("postgresql+psycopg://u:secret@localhost/db"))


def test_live_is_independent_of_database_and_lifespan_disposes() -> None:
    database = FakeDatabase(ErrorCode.DATABASE_UNAVAILABLE)
    with TestClient(create_app(config(), database=database)) as client:
        response = client.get("/health/live", headers={"X-Request-ID": "private-token"})
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}
        UUID(response.headers["X-Request-ID"])
        assert "private-token" not in str(response.headers)
        assert database.calls == 0
    assert database.closed


@pytest.mark.parametrize("error", [ErrorCode.DATABASE_UNAVAILABLE, ErrorCode.SCHEMA_NOT_READY])
def test_readiness_failure_has_stable_error_contract(error: ErrorCode) -> None:
    with TestClient(create_app(config(), database=FakeDatabase(error))) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    payload = ErrorResponse.model_validate(response.json())
    assert payload.code == error
    assert payload.retryable
    assert str(payload.request_id) == response.headers["X-Request-ID"]


def test_ready_succeeds_and_unknown_route_uses_envelope() -> None:
    with TestClient(create_app(config(), database=FakeDatabase())) as client:
        assert client.get("/health/ready").json() == {"status": "ready"}
        response = client.get("/private-query-token")
        assert response.status_code == 404
        assert response.json()["code"] == "not_found"
        assert "private-query-token" not in response.text


def test_validation_and_exceptions_never_return_private_details() -> None:
    app = create_app(config(), database=FakeDatabase())

    @app.get("/test/input")
    def input_route(value: int) -> int:
        return value

    @app.get("/test/crash")
    def crash_route() -> None:
        raise RuntimeError("postgresql://private-password@host/db")

    @app.get("/test/reject")
    def reject_route() -> None:
        raise HTTPException(status_code=403, detail="private-password")

    with TestClient(app) as client:
        for url, status in [
            ("/test/input?value=private-password", 422),
            ("/test/crash", 500),
            ("/test/reject", 403),
        ]:
            response = client.get(url)
            assert response.status_code == status
            assert "private-password" not in response.text
            ErrorResponse.model_validate(response.json())


def test_api_contains_only_foundation_routes() -> None:
    schema = create_app(config(), database=FakeDatabase()).openapi()
    assert set(schema["paths"]) == {"/health/live", "/health/ready"}
    responses = schema["paths"]["/health/ready"]["get"]["responses"]
    assert responses["503"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "ErrorResponse"
    )
    assert responses["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "HealthResponse"
    )
