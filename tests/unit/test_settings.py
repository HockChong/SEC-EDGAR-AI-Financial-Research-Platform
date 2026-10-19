from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from sec_research.settings import ConfigurationError, Settings, load_settings

LOCAL_URL = "postgresql+psycopg://app:private-password@localhost:5432/app"


def test_environment_loading_and_secret_safe_serialization(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", LOCAL_URL)
    monkeypatch.setenv("DB_POOL_SIZE", "2")
    monkeypatch.setenv("ARTIFACT_ROOT", "/tmp/artifacts")
    settings = load_settings()
    assert settings.db_pool_size == 2
    assert settings.artifact_root == Path("/tmp/artifacts")
    assert settings.database_url.get_secret_value() == LOCAL_URL
    assert "private-password" not in repr(settings)
    assert "private-password" not in settings.model_dump_json()


def test_missing_configuration_is_safe() -> None:
    with pytest.raises(ConfigurationError, match="Invalid application configuration") as result:
        load_settings()
    assert result.value.__suppress_context__


@pytest.mark.parametrize(
    "url",
    ["sqlite:///app.db", "bad-secret", "postgresql://u:p@host/db", "postgresql+psycopg:///db"],
)
def test_rejects_unsupported_database_urls(url: str) -> None:
    with pytest.raises(ValidationError):
        Settings(database_url=SecretStr(url))


@pytest.mark.parametrize(
    "name,value",
    [
        ("APP_ENV", "production"),
        ("DB_POOL_SIZE", "0"),
        ("DB_CONNECT_TIMEOUT", "31"),
        ("LOG_LEVEL", "password-is-private"),
    ],
)
def test_invalid_environment_does_not_echo_values(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv("DATABASE_URL", LOCAL_URL)
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigurationError) as result:
        load_settings()
    assert value not in str(result.value)
    assert "private-password" not in str(result.value)


def test_dotenv_not_implicitly_loaded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env").write_text(f"DATABASE_URL={LOCAL_URL}\n")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ConfigurationError):
        load_settings()
