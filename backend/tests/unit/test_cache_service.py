"""Unit tests for CacheService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cache_service import CacheService, _STATS_HITS, _STATS_MISSES


# ---------------------------------------------------------------------------
# Build key
# ---------------------------------------------------------------------------


def test_build_key_is_deterministic():
    svc = CacheService()
    k1 = svc.build_key("hello world", "gpt-4o-mini", 0.7, 1024)
    k2 = svc.build_key("hello world", "gpt-4o-mini", 0.7, 1024)
    assert k1 == k2


def test_build_key_differs_on_model():
    svc = CacheService()
    k1 = svc.build_key("prompt", "gpt-4o-mini", 0.7, 1024)
    k2 = svc.build_key("prompt", "claude-sonnet-4-6", 0.7, 1024)
    assert k1 != k2


def test_build_key_differs_on_temperature():
    svc = CacheService()
    k1 = svc.build_key("prompt", "gpt-4o-mini", 0.7, 1024)
    k2 = svc.build_key("prompt", "gpt-4o-mini", 0.0, 1024)
    assert k1 != k2


def test_build_key_normalises_whitespace():
    svc = CacheService()
    k1 = svc.build_key("hello  world", "model", 0.7, 1024)
    k2 = svc.build_key("hello world", "model", 0.7, 1024)
    assert k1 == k2


def test_build_key_has_cache_prefix():
    svc = CacheService()
    key = svc.build_key("test", "model", 0.5, 512)
    assert key.startswith("cache:")


# ---------------------------------------------------------------------------
# get — hit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_returns_value_on_hit():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="cached response")
    mock_redis.incr = AsyncMock()
    svc = CacheService(redis=mock_redis)

    result = await svc.get("cache:abc123")

    assert result == "cached response"
    mock_redis.incr.assert_called_once_with(_STATS_HITS)


@pytest.mark.asyncio
async def test_get_returns_none_on_miss():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.incr = AsyncMock()
    svc = CacheService(redis=mock_redis)

    result = await svc.get("cache:abc123")

    assert result is None
    mock_redis.incr.assert_called_once_with(_STATS_MISSES)


@pytest.mark.asyncio
async def test_get_returns_none_on_redis_error():
    from redis.exceptions import ConnectionError as RedisConnectionError
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(side_effect=RedisConnectionError("down"))
    svc = CacheService(redis=mock_redis)

    result = await svc.get("cache:abc123")

    assert result is None


# ---------------------------------------------------------------------------
# set
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_stores_value_with_ttl():
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()
    svc = CacheService(redis=mock_redis)

    await svc.set("cache:abc", "value", ttl=3600)

    mock_redis.set.assert_called_once_with("cache:abc", "value", ex=3600)


@pytest.mark.asyncio
async def test_set_swallows_redis_error():
    from redis.exceptions import ConnectionError as RedisConnectionError
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock(side_effect=RedisConnectionError("down"))
    svc = CacheService(redis=mock_redis)

    # Should not raise
    await svc.set("cache:abc", "value")


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_stats_computes_hit_rate():
    mock_redis = AsyncMock()
    mock_redis.mget = AsyncMock(return_value=["80", "20"])
    mock_redis.keys = AsyncMock(return_value=["cache:abc", "cache:def"])
    svc = CacheService(redis=mock_redis)

    stats = await svc.get_stats()

    assert stats["hits"] == 80
    assert stats["misses"] == 20
    assert stats["hit_rate"] == 0.8
    assert stats["total_requests_served"] == 100
    assert stats["cached_entries"] == 2


@pytest.mark.asyncio
async def test_get_stats_returns_zeros_on_redis_error():
    from redis.exceptions import ConnectionError as RedisConnectionError
    mock_redis = AsyncMock()
    mock_redis.mget = AsyncMock(side_effect=RedisConnectionError("down"))
    svc = CacheService(redis=mock_redis)

    stats = await svc.get_stats()

    assert stats["hit_rate"] == 0.0
    assert stats["hits"] == 0
