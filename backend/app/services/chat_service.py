"""
Chat orchestration service — Phase 1 stub.

Coordinates: rate limiting → cache check → routing → provider call
→ cost calculation → DB logging → response streaming.
Full implementation in Phase 2.
"""

from __future__ import annotations

# TODO(phase-2): Implement ChatService with:
#   - complete(request, user_id, db, redis) -> AsyncGenerator[str, None]
#   Flow:
#     1. RateLimitService.check_and_increment(user_id)
#     2. CacheService.get(prompt_hash) — return early on hit
#     3. RouterService.select_provider(strategy)
#     4. provider.call(normalized_request) — stream tokens
#     5. CostService.calculate(provider, model, tokens)
#     6. CacheService.set(prompt_hash, response)
#     7. RequestLogger.log(request_record)
