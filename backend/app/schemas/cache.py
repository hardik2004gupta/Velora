"""Cache analytics schemas."""

from __future__ import annotations

from app.schemas.common import VeloraBaseModel


class CacheStats(VeloraBaseModel):
    hits: int
    misses: int
    hit_rate: float
    total_requests_served: int
    cached_entries: int


class CacheClearResponse(VeloraBaseModel):
    cleared: int
    message: str
