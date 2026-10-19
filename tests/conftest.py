"""Offline by default; environment isolation prevents accidental use of user services."""

import pytest


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "APP_ENV",
        "DATABASE_URL",
        "ARTIFACT_ROOT",
        "LOG_LEVEL",
        "DB_CONNECT_TIMEOUT",
        "DB_POOL_SIZE",
    ):
        monkeypatch.delenv(name, raising=False)
