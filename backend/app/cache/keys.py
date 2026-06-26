"""
Redis key builders.

All Redis keys are constructed here to keep key patterns in one place.
Callers never construct keys by hand.

Key patterns (from CLAUDE.md):
    cache:{sha256_hash}              — prompt response cache
    rate:{user_id}:{minute_bucket}   — rate limit counter
    latency:{provider}               — rolling latency list
    health:{provider}                — health override flag
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from app.core.constants import (
    REDIS_PREFIX_CACHE,
    REDIS_PREFIX_HEALTH,
    REDIS_PREFIX_LATENCY,
    REDIS_PREFIX_RATE_LIMIT,
)


def prompt_cache_key(prompt_hash: str) -> str:
    """Return the Redis key for a cached prompt response."""
    return f"{REDIS_PREFIX_CACHE}:{prompt_hash}"


def rate_limit_key(user_id: str) -> str:
    """
    Return the Redis key for the current rate-limit window for *user_id*.

    Uses a per-minute bucket so the window resets automatically.
    """
    bucket = int(datetime.now(UTC).timestamp()) // 60
    return f"{REDIS_PREFIX_RATE_LIMIT}:{user_id}:{bucket}"


def provider_latency_key(provider: str) -> str:
    """Return the Redis key for the rolling latency list of *provider*."""
    return f"{REDIS_PREFIX_LATENCY}:{provider}"


def provider_health_key(provider: str) -> str:
    """Return the Redis key for the health-override flag of *provider*."""
    return f"{REDIS_PREFIX_HEALTH}:{provider}"


def build_prompt_hash(
    prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """
    Compute a deterministic SHA-256 hash for the given prompt parameters.

    The hash is used as the cache key suffix.  Whitespace in the prompt is
    normalised before hashing so trivially different inputs hit the same cache.
    """
    normalised_prompt = " ".join(prompt.split())
    raw = f"{normalised_prompt}:{model}:{temperature}:{max_tokens}"
    return hashlib.sha256(raw.encode()).hexdigest()
