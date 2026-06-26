"""Analytics response schemas."""

from __future__ import annotations

from app.schemas.common import VeloraBaseModel


class DashboardOverview(VeloraBaseModel):
    """Aggregated stats for the dashboard summary cards."""

    total_requests: int
    total_conversations: int
    avg_latency_ms: float
    total_cost_usd: float
    period_days: int
