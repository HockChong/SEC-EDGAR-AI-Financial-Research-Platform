"""Real database readiness without migrations or other startup mutations."""

from typing import Protocol

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from sec_research.contracts.errors import ErrorCode
from sec_research.settings import Settings

SCHEMA_HEAD = "0002_ingestion"
VECTOR_VERSION = "0.8.1"


class Database(Protocol):
    def readiness(self) -> ErrorCode | None: ...

    def close(self) -> None: ...


def create_database_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=0,
        pool_timeout=settings.db_connect_timeout,
        hide_parameters=True,
        connect_args={
            "connect_timeout": settings.db_connect_timeout,
            "options": "-c statement_timeout=5000",
        },
    )


class PostgresDatabase:
    def __init__(self, settings: Settings) -> None:
        self.engine = create_database_engine(settings)

    def readiness(self) -> ErrorCode | None:
        try:
            with self.engine.connect() as connection:
                revisions = (
                    connection.execute(text("SELECT version_num FROM alembic_version"))
                    .scalars()
                    .all()
                )
                vector_version = connection.execute(
                    text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                ).scalar_one_or_none()
                if revisions != [SCHEMA_HEAD] or vector_version != VECTOR_VERSION:
                    return ErrorCode.SCHEMA_NOT_READY
        except DBAPIError as error:
            if getattr(error.orig, "sqlstate", None) == "42P01":
                return ErrorCode.SCHEMA_NOT_READY
            return ErrorCode.DATABASE_UNAVAILABLE
        except SQLAlchemyError:
            return ErrorCode.DATABASE_UNAVAILABLE
        return None

    def close(self) -> None:
        self.engine.dispose()
