from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import text

from sec_research.adapters.postgres.database import SCHEMA_HEAD, PostgresDatabase
from sec_research.api.app import create_app
from sec_research.contracts.errors import ErrorCode
from sec_research.settings import Settings

pytestmark = pytest.mark.integration


def migration_config() -> Config:
    return Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))


def test_migration_rollback_reapply_preserves_vector_data(database_settings: Settings) -> None:
    db = PostgresDatabase(database_settings)
    try:
        assert db.readiness() == ErrorCode.SCHEMA_NOT_READY
        command.upgrade(migration_config(), "head")
        command.upgrade(migration_config(), "head")
        assert db.readiness() is None
        with db.engine.begin() as connection:
            connection.execute(text("CREATE TABLE preserved_vectors (embedding vector(3))"))
            connection.execute(text("INSERT INTO preserved_vectors VALUES ('[1,2,3]')"))
        command.downgrade(migration_config(), "base")
        assert db.readiness() == ErrorCode.SCHEMA_NOT_READY
        with db.engine.connect() as connection:
            distance = connection.execute(
                text("SELECT embedding <-> '[1,2,4]'::vector FROM preserved_vectors")
            ).scalar_one()
            assert distance == 1.0
        command.upgrade(migration_config(), "head")
        assert db.readiness() is None
        with db.engine.connect() as connection:
            assert (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == SCHEMA_HEAD
            )
    finally:
        db.close()


def test_actual_http_readiness_tracks_schema(database_settings: Settings) -> None:
    with TestClient(create_app(database_settings)) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503
        command.upgrade(migration_config(), "head")
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}


@pytest.mark.parametrize(
    "mutation", ["UPDATE alembic_version SET version_num = 'incompatible'", "DROP EXTENSION vector"]
)
def test_incompatible_schema_or_missing_extension_not_ready(
    database_settings: Settings, mutation: str
) -> None:
    command.upgrade(migration_config(), "head")
    db = PostgresDatabase(database_settings)
    try:
        with db.engine.begin() as connection:
            connection.execute(text(mutation))
        assert db.readiness() == ErrorCode.SCHEMA_NOT_READY
    finally:
        db.close()


def test_unreachable_database_returns_safe_failure() -> None:
    settings = Settings(
        database_url=SecretStr("postgresql+psycopg://u:private@127.0.0.1:1/unreachable"),
        db_connect_timeout=1,
    )
    db = PostgresDatabase(settings)
    try:
        assert db.readiness() == ErrorCode.DATABASE_UNAVAILABLE
    finally:
        db.close()
