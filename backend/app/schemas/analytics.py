"""Analytics response schemas — Phase 5."""

from __future__ import annotations

from app.schemas.common import VeloraBaseModel


class DashboardOverview(VeloraBaseModel):
    """Aggregated stats for the dashboard summary cards."""

    total_requests: int
    total_conversations: int
    avg_latency_ms: float
    total_cost_usd: float
    period_days: int


# ---------------------------------------------------------------------------
# Cost over time
# ---------------------------------------------------------------------------


class CostDataPoint(VeloraBaseModel):
    date: str  # "2025-01-15"
    cost: float  # total across all providers
    openai: float = 0.0
    anthropic: float = 0.0
    gemini: float = 0.0


class CostOverTime(VeloraBaseModel):
    data: list[CostDataPoint]
    period_days: int
    total: float


# ---------------------------------------------------------------------------
# Latency analytics
# ---------------------------------------------------------------------------


class LatencyDataPoint(VeloraBaseModel):
    date: str
    avg_ms: float


class LatencyAnalytics(VeloraBaseModel):
    data: list[LatencyDataPoint]  # daily averages for line chart
    avg_ms: float
    p50_ms: float | None
    p95_ms: float | None
    by_provider: dict[str, float]  # provider → avg latency ms
    period_days: int


# ---------------------------------------------------------------------------
# Provider distribution
# ---------------------------------------------------------------------------


class ProviderStat(VeloraBaseModel):
    provider: str
    requests: int
    percentage: float
    cost: float
    avg_latency_ms: float | None
    success_rate: float


class ProviderDistribution(VeloraBaseModel):
    providers: list[ProviderStat]
    period_days: int
    total_requests: int


# ---------------------------------------------------------------------------
# Token analytics
# ---------------------------------------------------------------------------


class TokenAnalytics(VeloraBaseModel):
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    avg_per_request: float
    period_days: int


# ---------------------------------------------------------------------------
# Conversation analytics
# ---------------------------------------------------------------------------


class ConversationAnalytics(VeloraBaseModel):
    total_conversations: int
    avg_messages_per_conversation: float
    period_days: int


# ---------------------------------------------------------------------------
# Routing insights
# ---------------------------------------------------------------------------


class RoutingInsights(VeloraBaseModel):
    strategy_distribution: dict[str, int]
    most_used_strategy: str
    most_selected_provider: str
    period_days: int
