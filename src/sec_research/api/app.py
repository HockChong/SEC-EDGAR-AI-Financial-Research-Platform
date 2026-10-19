"""Foundation API: health endpoints only; no research features or migration side effects."""

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import UUID, uuid4

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from sec_research.adapters.postgres.database import Database, PostgresDatabase
from sec_research.contracts.errors import ErrorCode, ErrorResponse
from sec_research.contracts.health import HealthResponse
from sec_research.observability.logging import Event, configure_logging
from sec_research.settings import Settings, load_settings

logger = logging.getLogger(__name__)


def error_response(
    request_id: UUID, code: ErrorCode, message: str, *, status: int, retryable: bool = False
) -> JSONResponse:
    error = ErrorResponse(code=code, message=message, retryable=retryable, request_id=request_id)
    return JSONResponse(status_code=status, content=error.model_dump(mode="json"))


def create_app(settings: Settings | None = None, *, database: Database | None = None) -> FastAPI:
    config = settings if settings is not None else load_settings()
    db = database if database is not None else PostgresDatabase(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            db.close()

    app = FastAPI(title="SEC Research Foundation", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Generate server-owned correlation IDs; never echo arbitrary incoming header contents.
        request_id = uuid4()
        request.state.request_id = request_id
        started = perf_counter()
        event = Event.REQUEST_COMPLETED
        try:
            response = await call_next(request)
        except Exception:
            event = Event.REQUEST_FAILED
            response = error_response(
                request_id, ErrorCode.INTERNAL_ERROR, "Request failed.", status=500
            )
        response.headers["X-Request-ID"] = str(request_id)
        logger.info(
            "",
            extra={
                "event": event,
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": (perf_counter() - started) * 1000,
            },
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(
            request.state.request_id, ErrorCode.INVALID_REQUEST, "Invalid request.", status=422
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        code = ErrorCode.NOT_FOUND if exc.status_code == 404 else ErrorCode.HTTP_ERROR
        return error_response(
            request.state.request_id, code, "Request rejected.", status=exc.status_code
        )

    @app.get("/health/live", response_model=HealthResponse)
    def live() -> HealthResponse:
        return HealthResponse(status="alive")

    @app.get(
        "/health/ready", response_model=HealthResponse, responses={503: {"model": ErrorResponse}}
    )
    def ready(request: Request) -> HealthResponse | JSONResponse:
        result = db.readiness()
        if result is not None:
            return error_response(
                request.state.request_id,
                result,
                "Database or schema is not ready.",
                status=503,
                retryable=True,
            )
        return HealthResponse(status="ready")

    return app


def app_factory() -> FastAPI:
    settings = load_settings()
    configure_logging(settings.log_level)
    return create_app(settings)
