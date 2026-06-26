"""
Rate limiting service — Phase 1 stub.

Fixed-window per-user rate limiting backed by Redis.
Full implementation in Phase 2.
"""

from __future__ import annotations

# TODO(phase-2): Implement RateLimitService with:
#   - check_and_increment(user_id) -> None  (raises RateLimitExceededError)
#   - get_remaining(user_id) -> int
#   Uses INCR + EXPIRE pattern with rate:{user_id}:{minute_bucket} keys.
