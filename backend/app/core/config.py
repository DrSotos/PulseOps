"""Application configuration loaded from environment variables."""

from __future__ import annotations

from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for PulseOps.

    All values are loaded from environment variables or a .env file.
    """

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "PulseOps"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-to-a-random-secret-key-at-least-32-chars"
    API_PREFIX: str = "/api/v1"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on", "t", "dev", "development")
        return bool(v)

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://pulseops:pulseops_dev@localhost:5432/pulseops"
    )
    DATABASE_ECHO: bool = False

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Authentication / JWT ─────────────────────────────────────────────
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # ── Monitoring ───────────────────────────────────────────────────────
    MAX_CONCURRENT_CHECKS: int = 20
    DEFAULT_CHECK_INTERVAL: int = 60
    DEFAULT_CHECK_TIMEOUT: int = 10
    MIN_CHECK_INTERVAL: int = 30
    MAX_CHECK_INTERVAL: int = 900
    START_EMBEDDED_WORKER: bool = True
    SERVE_FRONTEND: bool = True

    # ── SSRF Protection ──────────────────────────────────────────────────
    ALLOW_PRIVATE_NETWORKS: bool = False

    # ── Notifications – Email ────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    # ── Notifications – Webhook ──────────────────────────────────────────
    WEBHOOK_TIMEOUT: int = 10
    WEBHOOK_MAX_RETRIES: int = 3

    # ── Incident Detection ───────────────────────────────────────────────
    INCIDENT_FAILURE_THRESHOLD: int = 3
    INCIDENT_RECOVERY_THRESHOLD: int = 2

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list of strings."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """Check if the application is running in production."""
        return self.APP_ENV == "production"

    @model_validator(mode="after")
    def validate_database_url(self) -> Settings:
        """Ensure the DATABASE_URL uses the asyncpg driver."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            self.DATABASE_URL = url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        elif url.startswith("postgres://"):
            self.DATABASE_URL = url.replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        return self

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


# Global singleton – import this everywhere
settings = Settings()
