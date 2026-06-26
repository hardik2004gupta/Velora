"""
Rate limiting middleware — placeholder.

Rate limiting is implemented in ``app/services/rate_limit_service.py`` and
applied per-route via a FastAPI dependency.  This file is reserved for a
future global middleware implementation (e.g., IP-based limiting for
unauthenticated endpoints).
"""

from __future__ import annotations

# TODO(phase-2): Implement IP-level rate limiting for unauthenticated endpoints.
# Per-user rate limiting is handled by RateLimitService inside chat routes.
