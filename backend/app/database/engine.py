"""
Async SQLAlchemy engine factory.

The engine is created lazily on first access.  Connection pool settings are
sourced from ``Settings`` so they can be tuned per environment without code
changes.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


def _build_engine() -> AsyncEngine:
    """Build and return the async SQLAlchemy engine."""
    settings = get_settings()

    engine = create_async_engine(
        settings.database_url_str,
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        pool_pre_ping=True,  # validate connections before use
        pool_recycle=3600,   # recycle connections hourly
    )

    log.info(
        "database_engine_created",
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )
    return engine


# Module-level singleton — created once at import time.
engine: AsyncEngine = _build_engine()
