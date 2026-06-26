"""Redis client dependency."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends
from redis.asyncio import Redis

from app.cache.client import get_redis_client


async def get_redis(
    redis: Redis = Depends(get_redis_client),  # type: ignore[type-arg]
) -> AsyncGenerator[Redis, None]:  # type: ignore[type-arg]
    """
    FastAPI dependency that yields an async Redis client.

    Routes use this as ``Depends(get_redis)``.
    """
    yield redis
