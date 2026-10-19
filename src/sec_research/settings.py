"""Typed, explicit configuration; importing this module performs no environment reads."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class ConfigurationError(Exception):
    """Safe startup failure without input values or exception details."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        frozen=True,
        hide_input_in_errors=True,
    )

    # Shared/production exposure requires Phase 7 authentication and is deliberately unsupported.
    app_env: Literal["development", "test"] = "development"
    database_url: SecretStr
    artifact_root: Path = Path(".runtime/artifacts")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    db_connect_timeout: int = Field(default=3, ge=1, le=30)
    db_pool_size: int = Field(default=5, ge=1, le=20)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        try:
            url = make_url(value.get_secret_value())
            valid = (
                url.drivername == "postgresql+psycopg"
                and bool(url.host)
                and bool(url.username)
                and bool(url.database)
            )
        except (ArgumentError, ValueError):
            valid = False
        if not valid:
            raise ValueError(
                "DATABASE_URL must specify a psycopg PostgreSQL host, user and database"
            )
        return value


def load_settings() -> Settings:
    """Load process variables only. Never echo invalid values in startup errors."""
    try:
        return Settings()  # type: ignore[call-arg]  # Required fields come from the environment.
    except ValidationError:
        raise ConfigurationError(
            "Invalid application configuration; check environment settings."
        ) from None
