"""Create and destroy uniquely named databases; never migrate the configured database."""

import os
from collections.abc import Iterator
from uuid import uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from sec_research.settings import Settings


@pytest.fixture
def database_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[Settings]:
    raw_url = os.environ.get("TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    url = make_url(raw_url)
    if not url.database or not url.database.endswith("_test"):
        pytest.fail("TEST_DATABASE_URL must name a dedicated database ending in _test")
    database_name = f"sec_test_{uuid4().hex}"
    admin = create_engine(url, isolation_level="AUTOCOMMIT", hide_parameters=True)
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    test_url = url.set(database=database_name).render_as_string(hide_password=False)
    monkeypatch.setenv("DATABASE_URL", test_url)
    try:
        yield Settings(database_url=SecretStr(test_url), app_env="test")
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{database_name}" WITH (FORCE)'))
        admin.dispose()
