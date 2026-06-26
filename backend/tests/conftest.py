"""
Pytest configuration and shared fixtures.

Fixtures are grouped by scope:
- session scope: DB engine, test database creation
- function scope: DB session (rolled back after each test), HTTP test client

Environment:
    Set ENVIRONMENT=test in .env.test or export it before running tests.
    The test database URL should point to a separate test database.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Force test environment before importing app modules
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/velora_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production-use-at-all")
os.environ.setdefault("LOG_FORMAT", "console")
os.environ.setdefault("LOG_LEVEL", "WARNING")

from app.config import get_settings
from app.database.base import Base
from app.database.session import get_db_session
from app.main import create_app


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create the test database schema at the start of the test session and
    drop it at the end.
    """
    settings = get_settings()
    engine = create_async_engine(settings.database_url_str, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async session that is rolled back after each test.

    This keeps each test independent without needing to truncate tables.
    """
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


# ---------------------------------------------------------------------------
# Redis mock fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Return a mock Redis client for unit tests that don't need real Redis."""
    redis = AsyncMock()
    redis.ping.return_value = True
    redis.get.return_value = None
    redis.set.return_value = True
    redis.incr.return_value = 1
    redis.expire.return_value = True
    return redis


# ---------------------------------------------------------------------------
# HTTP client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
async def app(db_session: AsyncSession, mock_redis: AsyncMock) -> FastAPI:
    """
    Return a FastAPI test application with overridden dependencies.

    Database and Redis dependencies are replaced with test versions.
    """
    # Clear the settings cache so test env vars take effect
    get_settings.cache_clear()

    test_app = create_app()

    async def override_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_redis() -> AsyncGenerator[Any, None]:
        yield mock_redis

    from app.cache.client import get_redis_client
    from app.database.session import get_db_session as get_db

    test_app.dependency_overrides[get_db] = override_db
    test_app.dependency_overrides[get_redis_client] = override_redis

    return test_app


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Yield an async HTTP test client for the test application.

    Uses httpx with ASGI transport — no real network calls.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """
    Return valid JWT Authorization headers for a test user.

    Uses the test JWT secret to create a valid token.
    """
    from app.core.security import create_access_token

    token = create_access_token(subject="test-user-uuid")
    return {"Authorization": f"Bearer {token}"}
