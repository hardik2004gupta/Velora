"""Fixed-window per-user rate limiter backed by Redis."""

from __future__ import annotations

import uuid

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.cache.client import get_client
from app.cache.keys import rate_limit_key
from app.config import get_settings
from app.core.exceptions import CacheError, RateLimitExceededError
from app.core.logging import get_logger

log = get_logger(__name__)


class RateLimitService:
    def __init__(self, redis: Redis | None = None) -> None:  # type: ignore[type-arg]
        self._redis = redis

    def _get_redis(self) -> Redis:  # type: ignore[type-arg]
        if self._redis is not None:
            return self._redis
        return get_client()

    async def check_and_increment(self, user_id: uuid.UUID | str) -> None:
        """Increment request counter and raise RateLimitExceededError if over limit.

        Fails open — if Redis is unavailable, the request is allowed through.
        """
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return

        key = rate_limit_key(str(user_id))
        limit = settings.rate_limit_per_minute
        try:
            r = self._get_redis()
            count = await r.incr(key)
            if count == 1:
                # First request in this window — set TTL
                await r.expire(key, 60)
            if count > limit:
                raise RateLimitExceededError(retry_after_seconds=60)
        except RateLimitExceededError:
            raise
        except (RedisError, CacheError) as exc:
            log.warning("rate_limit_check_failed", user_id=str(user_id), error=str(exc))

    async def get_remaining(self, user_id: uuid.UUID | str) -> int:
        """Return how many requests remain in the current window."""
        settings = get_settings()
        limit = settings.rate_limit_per_minute
        key = rate_limit_key(str(user_id))
        try:
            r = self._get_redis()
            raw = await r.get(key)
            current = int(raw or 0)
            return max(0, limit - current)
        except (RedisError, CacheError) as exc:
            log.warning("rate_limit_remaining_failed", user_id=str(user_id), error=str(exc))
            return limit
