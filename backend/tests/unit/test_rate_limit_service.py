"""Unit tests for RateLimitService."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import RateLimitExceededError
from app.services.rate_limit_service import RateLimitService


USER_ID = uuid.uuid4()


# ---------------------------------------------------------------------------
# check_and_increment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_allows_request_within_limit():
    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock()

    with patch("app.services.rate_limit_service.get_settings") as mock_settings:
        mock_settings.return_value.rate_limit_enabled = True
        mock_settings.return_value.rate_limit_per_minute = 20
        svc = RateLimitService(redis=mock_redis)
        await svc.check_and_increment(USER_ID)  # should not raise


@pytest.mark.asyncio
async def test_sets_expire_on_first_request():
    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock()

    with patch("app.services.rate_limit_service.get_settings") as mock_settings:
        mock_settings.return_value.rate_limit_enabled = True
        mock_settings.return_value.rate_limit_per_minute = 20
        svc = RateLimitService(redis=mock_redis)
        await svc.check_and_increment(USER_ID)

    mock_redis.expire.assert_called_once()
    args = mock_redis.expire.call_args[0]
    assert args[1] == 60  # 60 second window


@pytest.mark.asyncio
async def test_does_not_set_expire_on_subsequent_requests():
    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=5)  # already incremented
    mock_redis.expire = AsyncMock()

    with patch("app.services.rate_limit_service.get_settings") as mock_settings:
        mock_settings.return_value.rate_limit_enabled = True
        mock_settings.return_value.rate_limit_per_minute = 20
        svc = RateLimitService(redis=mock_redis)
        await svc.check_and_increment(USER_ID)

    mock_redis.expire.assert_not_called()


@pytest.mark.asyncio
async def test_raises_when_over_limit():
    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=21)
    mock_redis.expire = AsyncMock()

    with patch("app.services.rate_limit_service.get_settings") as mock_settings:
        mock_settings.return_value.rate_limit_enabled = True
        mock_settings.return_value.rate_limit_per_minute = 20
        svc = RateLimitService(redis=mock_redis)

        with pytest.raises(RateLimitExceededError):
            await svc.check_and_increment(USER_ID)


@pytest.mark.asyncio
async def test_skips_when_disabled():
    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=9999)

    with patch("app.services.rate_limit_service.get_settings") as mock_settings:
        mock_settings.return_value.rate_limit_enabled = False
        svc = RateLimitService(redis=mock_redis)
        await svc.check_and_increment(USER_ID)  # should not raise

    mock_redis.incr.assert_not_called()


@pytest.mark.asyncio
async def test_fails_open_on_redis_error():
    from redis.exceptions import ConnectionError as RedisConnectionError
    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(side_effect=RedisConnectionError("down"))

    with patch("app.services.rate_limit_service.get_settings") as mock_settings:
        mock_settings.return_value.rate_limit_enabled = True
        mock_settings.return_value.rate_limit_per_minute = 20
        svc = RateLimitService(redis=mock_redis)
        await svc.check_and_increment(USER_ID)  # should not raise — fail open


# ---------------------------------------------------------------------------
# get_remaining
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_remaining_computes_correctly():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value="15")

    with patch("app.services.rate_limit_service.get_settings") as mock_settings:
        mock_settings.return_value.rate_limit_per_minute = 20
        svc = RateLimitService(redis=mock_redis)
        remaining = await svc.get_remaining(USER_ID)

    assert remaining == 5


@pytest.mark.asyncio
async def test_get_remaining_returns_full_limit_on_error():
    from redis.exceptions import ConnectionError as RedisConnectionError
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(side_effect=RedisConnectionError("down"))

    with patch("app.services.rate_limit_service.get_settings") as mock_settings:
        mock_settings.return_value.rate_limit_per_minute = 20
        svc = RateLimitService(redis=mock_redis)
        remaining = await svc.get_remaining(USER_ID)

    assert remaining == 20
