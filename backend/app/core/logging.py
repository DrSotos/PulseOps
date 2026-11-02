"""Structured logging setup for PulseOps."""

from __future__ import annotations

import logging
import sys

from app.core.config import settings

# ── Format ───────────────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def _resolve_log_level() -> int:
    """Return the root log level based on the environment."""
    if settings.DEBUG:
        return logging.DEBUG
    if settings.is_production:
        return logging.WARNING
    return logging.INFO


def setup_logging() -> None:
    """Configure the root logger with a consistent format.

    Should be called once at application startup.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(_resolve_log_level())

    # Remove any existing handlers to avoid duplicate output
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(_resolve_log_level())
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root_logger.addHandler(handler)

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DATABASE_ECHO else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A :class:`logging.Logger` configured by :func:`setup_logging`.
    """
    return logging.getLogger(name)
