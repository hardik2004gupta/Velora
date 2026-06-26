"""
Application configuration via Pydantic Settings.

All configuration is loaded from environment variables (or a .env file in
development).  Values are validated at startup — the application will refuse
to start if required variables are missing or invalid.

Usage::

    from app.config import get_settings

    settings = get_settings()
    print(settings.app_name)
"""

from __future__ import annotations

import secrets
from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Deployment environment identifier."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


class LogFormat(StrEnum):
    """Structured log output format."""

    JSON = "json"
    CONSOLE = "console"


class Settings(BaseSettings):
    """
    Central application settings.

    All fields are sourced from environment variables.  Field names map
    directly to env var names (case-insensitive).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    app_name: str = "Velora"
    app_version: str = "0.1.0"
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(64))

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: PostgresDsn
    database_pool_size: Annotated[int, Field(ge=1, le=50)] = 10
    database_max_overflow: Annotated[int, Field(ge=0, le=50)] = 20
    database_pool_timeout: Annotated[int, Field(ge=1)] = 30
    database_echo: bool = False

    # -------------------------------------------------------------------------
    # Redis
    # -------------------------------------------------------------------------
    redis_url: RedisDsn
    redis_max_connections: Annotated[int, Field(ge=1, le=100)] = 20
    redis_socket_timeout: Annotated[int, Field(ge=1)] = 5

    # -------------------------------------------------------------------------
    # JWT
    # -------------------------------------------------------------------------
    jwt_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: Annotated[int, Field(ge=1)] = 15
    jwt_refresh_token_expire_days: Annotated[int, Field(ge=1)] = 30

    # -------------------------------------------------------------------------
    # Provider API keys (optional at startup — validated per-request)
    # -------------------------------------------------------------------------
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None

    # -------------------------------------------------------------------------
    # Rate limiting
    # -------------------------------------------------------------------------
    rate_limit_per_minute: Annotated[int, Field(ge=1)] = 20
    rate_limit_enabled: bool = True

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    log_level: str = "INFO"
    log_format: LogFormat = LogFormat.CONSOLE

    # -------------------------------------------------------------------------
    # Background tasks
    # -------------------------------------------------------------------------
    health_check_interval_seconds: Annotated[int, Field(ge=10)] = 60
    provider_health_check_timeout: Annotated[int, Field(ge=1)] = 5

    # -------------------------------------------------------------------------
    # Telemetry
    # -------------------------------------------------------------------------
    otel_enabled: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "velora-backend"

    # -------------------------------------------------------------------------
    # Computed properties
    # -------------------------------------------------------------------------

    @property
    def is_development(self) -> bool:
        """True when running in development mode."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """True when running in production mode."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_test(self) -> bool:
        """True when running under the test suite."""
        return self.environment == Environment.TEST

    @property
    def database_url_str(self) -> str:
        """Return the database URL as a plain string."""
        return str(self.database_url)

    @property
    def redis_url_str(self) -> str:
        """Return the Redis URL as a plain string."""
        return str(self.redis_url)

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Accept either a comma-separated string or a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is a valid Python logging level name."""
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}, got {v!r}")
        return upper


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings singleton.

    Uses ``lru_cache`` so the environment is only parsed once per process.
    In tests, call ``get_settings.cache_clear()`` after overriding env vars.
    """
    return Settings()
