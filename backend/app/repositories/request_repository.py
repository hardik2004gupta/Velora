"""Request repository — Phase 1 stub."""

from __future__ import annotations

from app.models.request import Request
from app.repositories.base import BaseRepository


class RequestRepository(BaseRepository[Request]):
    """Data access for the requests table."""

    model = Request

    # TODO(phase-2): Add domain-specific queries:
    #   - get_by_user(user_id, page, limit, filters) -> tuple[list[Request], int]
    #   - get_cost_over_time(user_id, start, end) -> list[DailyCost]
    #   - get_provider_distribution(user_id, start, end) -> dict[str, int]
    #   - get_latency_over_time(user_id, start, end) -> list[DailyLatency]
