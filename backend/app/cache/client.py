"""
Async Redis client manager.

A single ``redis.asyncio.ConnectionPool`` is shared across the process.
The pool is created during application startup and closed during shutdown
via the lifespan handler.

FastAPI dependency usage::

    from fastapi import Depends
    from redis.asyncio import Redis

    from app.cache.client import get_redis_client

    @router.get("/example")
    async def example(redis: Redis = Depends(get_redis_client)):
        value = await redis.get("some-key")
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError

from app.config import get_settings
from app.core.exceptions import CacheError
from app.core.logging import get_logger

log = get_logger(__name__)

# Module-level pool — initialised in ``setup()`` and closed in ``teardown()``.
_pool: ConnectionPool | None = None


def setup() -> None:
    """
    Create the Redis connection pool.

    Must be called once during application startup (lifespan handler).
    """
    global _pool  # noqa: PLW0603

    settings = get_settings()

    _pool = aioredis.ConnectionPool.from_url(
        settings.redis_url_str,
        max_connections=settings.redis_max_connections,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_timeout,
        decode_responses=True,
        health_check_interval=30,
    )

    log.info(
        "redis_pool_created",
        max_connections=settings.redis_max_connections,
    )


async def teardown() -> None:
    """
    Close the Redis connection pool.

    Must be called during application shutdown (lifespan handler).
    """
    global _pool  # noqa: PLW0603

    if _pool is not None:
        await _pool.aclose()
        _pool = None
        log.info("redis_pool_closed")


def get_client() -> Redis:  # type: ignore[type-arg]
    """
    Return an async Redis client bound to the shared pool.

    Raises:
        CacheError: If the pool has not been initialised yet.
    """
    if _pool is None:
        raise CacheError("Redis pool is not initialised. Call cache.client.setup() first.")
    return Redis(connection_pool=_pool)


async def get_redis_client() -> AsyncGenerator[Redis, None]:  # type: ignore[type-arg]
    """
    FastAPI dependency that yields a Redis client.

    The client is borrowed from the shared connection pool and is safe to
    use for the duration of the request.
    """
    client = get_client()
    try:
        yield client
    finally:
        await client.aclose()


class RedisClient:
    """
    Thin wrapper around ``redis.asyncio.Redis`` with error normalisation.

    Wraps ``RedisError`` into ``CacheError`` so callers don't need to import
    from the redis package.
    """

    def __init__(self, client: Redis) -> None:  # type: ignore[type-arg]
        self._client = client

    async def get(self, key: str) -> str | None:
        """Return the string value at *key*, or None if missing."""
        try:
            return await self._client.get(key)  # type: ignore[no-any-return]
        except RedisError as exc:
            raise CacheError(f"GET {key} failed: {exc}") from exc

    async def set(
        self,
        key: str,
        value: str,
        *,
        ex: int | None = None,
    ) -> None:
        """Set *key* to *value* with an optional expiry in seconds."""
        try:
            await self._client.set(key, value, ex=ex)
        except RedisError as exc:
            raise CacheError(f"SET {key} failed: {exc}") from exc

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys.  Returns the number of keys removed."""
        try:
            return await self._client.delete(*keys)  # type: ignore[no-any-return]
        except RedisError as exc:
            raise CacheError(f"DEL {keys} failed: {exc}") from exc

    async def incr(self, key: str) -> int:
        """Atomically increment *key* by 1 and return the new value."""
        try:
            return await self._client.incr(key)  # type: ignore[no-any-return]
        except RedisError as exc:
            raise CacheError(f"INCR {key} failed: {exc}") from exc

    async def expire(self, key: str, seconds: int) -> bool:
        """Set TTL on *key*.  Returns True if the key exists."""
        try:
            return await self._client.expire(key, seconds)  # type: ignore[no-any-return]
        except RedisError as exc:
            raise CacheError(f"EXPIRE {key} failed: {exc}") from exc

    async def lpush(self, key: str, *values: Any) -> int:
        """Prepend *values* to the list at *key*."""
        try:
            return await self._client.lpush(key, *values)  # type: ignore[no-any-return]
        except RedisError as exc:
            raise CacheError(f"LPUSH {key} failed: {exc}") from exc

    async def ltrim(self, key: str, start: int, end: int) -> None:
        """Trim list at *key* to the range [start, end]."""
        try:
            await self._client.ltrim(key, start, end)
        except RedisError as exc:
            raise CacheError(f"LTRIM {key} failed: {exc}") from exc

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        """Return a slice of the list at *key*."""
        try:
            return await self._client.lrange(key, start, end)  # type: ignore[no-any-return]
        except RedisError as exc:
            raise CacheError(f"LRANGE {key} failed: {exc}") from exc

    async def ping(self) -> bool:
        """Return True if Redis responds to a PING command."""
        try:
            response = await self._client.ping()
            return bool(response)
        except RedisError:
            return False
