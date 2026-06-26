"""Analytics response schemas."""

from __future__ import annotations

from datetime import date

from app.schemas.common import VeloraBaseModel


class OverviewResponse(VeloraBaseModel):
    """Response for GET /analytics/overview."""

    total_requests: int
    total_cost_usd: float
    avg_latency_ms: float
    cache_hit_rate: float
    by_provider: dict[str, int]
    by_status: dict[str, int]


class DailyCostPoint(VeloraBaseModel):
    """Single data point for the cost-over-time chart."""

    date: date
    cost_usd: float


class CostOverTimeResponse(VeloraBaseModel):
    """Response for GET /analytics/cost-over-time."""

    data: list[DailyCostPoint]


class DailyLatencyPoint(VeloraBaseModel):
    """Single data point for latency-over-time chart."""

    date: date
    provider: str
    avg_latency_ms: float


class LatencyOverTimeResponse(VeloraBaseModel):
    """Response for GET /analytics/latency-over-time."""

    data: list[DailyLatencyPoint]


class ProviderDistributionPoint(VeloraBaseModel):
    """Single provider's share in the distribution chart."""

    provider: str
    count: int
    percentage: float


class ProviderDistributionResponse(VeloraBaseModel):
    """Response for GET /analytics/provider-distribution."""

    data: list[ProviderDistributionPoint]
