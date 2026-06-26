"""
Cache service — Phase 1 stub.

Wraps Redis prompt caching with get/set/hash operations.
Full implementation in Phase 2.
"""

from __future__ import annotations

# TODO(phase-2): Implement CacheService with:
#   - get(prompt_hash, model, temperature, max_tokens) -> str | None
#   - set(prompt_hash, model, temperature, max_tokens, response) -> None
#   - build_hash(prompt, model, temperature, max_tokens) -> str
#   Uses app.cache.keys.build_prompt_hash for deterministic key construction.
