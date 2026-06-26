"""Prompt cache service backed by Redis."""

from __future__ import annotations

from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.cache.client import get_client
from app.cache.keys import build_prompt_hash, prompt_cache_key
from app.core.exceptions import CacheError
from app.core.logging import get_logger

log = get_logger(__name__)

_STATS_HITS = "cache:stats:hits"
_STATS_MISSES = "cache:stats:misses"
_CACHE_TTL = 3600  # 1 hour


class CacheService:
    def __init__(self, redis: Redis | None = None) -> None:  # type: ignore[type-arg]
        self._redis = redis

    def _get_redis(self) -> Redis:  # type: ignore[type-arg]
        if self._redis is not None:
            return self._redis
        return get_client()

    def build_key(self, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        h = build_prompt_hash(prompt, model, temperature, max_tokens)
        return prompt_cache_key(h)

    async def get(self, key: str) -> str | None:
        try:
            r = self._get_redis()
            value = await r.get(key)
            if value is not None:
                await r.incr(_STATS_HITS)
                return str(value)
            await r.incr(_STATS_MISSES)
            return None
        except (RedisError, CacheError) as exc:
            log.warning("cache_get_failed", key=key, error=str(exc))
            return None

    async def set(self, key: str, value: str, ttl: int = _CACHE_TTL) -> None:
        try:
            r = self._get_redis()
            await r.set(key, value, ex=ttl)
        except (RedisError, CacheError) as exc:
            log.warning("cache_set_failed", key=key, error=str(exc))

    async def clear(self) -> int:
        """Delete all cache:{...} response keys. Returns count deleted."""
        try:
            r = self._get_redis()
            # Only delete prompt cache keys, not stat keys
            keys = await r.keys("cache:[a-f0-9]*")
            if not keys:
                # Fallback: scan for all cache: keys that aren't stats
                all_cache = await r.keys("cache:*")
                keys = [k for k in all_cache if not k.startswith("cache:stats")]
            if not keys:
                return 0
            return await r.delete(*keys)
        except (RedisError, CacheError) as exc:
            log.warning("cache_clear_failed", error=str(exc))
            return 0

    async def get_stats(self) -> dict[str, Any]:
        try:
            r = self._get_redis()
            hits_raw, misses_raw = await r.mget(_STATS_HITS, _STATS_MISSES)
            hits = int(hits_raw or 0)
            misses = int(misses_raw or 0)
            total = hits + misses
            all_keys = await r.keys("cache:*")
            cache_entries = [k for k in all_keys if not k.startswith("cache:stats")]
            return {
                "hits": hits,
                "misses": misses,
                "hit_rate": round(hits / total, 4) if total else 0.0,
                "total_requests_served": total,
                "cached_entries": len(cache_entries),
            }
        except (RedisError, CacheError) as exc:
            log.warning("cache_stats_failed", error=str(exc))
            return {
                "hits": 0,
                "misses": 0,
                "hit_rate": 0.0,
                "total_requests_served": 0,
                "cached_entries": 0,
            }
