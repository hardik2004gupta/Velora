"""Unit tests for AnalyticsService schema correctness and pure computation helpers."""

from __future__ import annotations

import pytest

from app.schemas.analytics import (
    ConversationAnalytics,
    CostDataPoint,
    CostOverTime,
    LatencyAnalytics,
    LatencyDataPoint,
    ProviderDistribution,
    ProviderStat,
    RoutingInsights,
    TokenAnalytics,
)


# ---------------------------------------------------------------------------
# CostDataPoint
# ---------------------------------------------------------------------------


def test_cost_data_point_defaults_to_zero():
    pt = CostDataPoint(date="2025-01-01", cost=0.0)
    assert pt.openai == 0.0
    assert pt.anthropic == 0.0
    assert pt.gemini == 0.0


def test_cost_data_point_stores_providers():
    pt = CostDataPoint(
        date="2025-01-15",
        cost=0.0015,
        openai=0.001,
        anthropic=0.0005,
        gemini=0.0,
    )
    assert pt.openai == 0.001
    assert pt.anthropic == 0.0005
    assert pt.cost == 0.0015


def test_cost_over_time_aggregates():
    pts = [
        CostDataPoint(date="2025-01-01", cost=0.001, openai=0.001),
        CostDataPoint(date="2025-01-02", cost=0.002, anthropic=0.002),
    ]
    result = CostOverTime(data=pts, period_days=7, total=0.003)
    assert result.total == 0.003
    assert len(result.data) == 2


# ---------------------------------------------------------------------------
# ProviderStat
# ---------------------------------------------------------------------------


def test_provider_stat_nullable_latency():
    stat = ProviderStat(
        provider="gemini",
        requests=10,
        percentage=10.0,
        cost=0.001,
        avg_latency_ms=None,
        success_rate=100.0,
    )
    assert stat.avg_latency_ms is None


def test_provider_stat_success_rate_range():
    stat = ProviderStat(
        provider="openai",
        requests=100,
        percentage=80.0,
        cost=0.05,
        avg_latency_ms=820.0,
        success_rate=95.0,
    )
    assert 0.0 <= stat.success_rate <= 100.0


@pytest.mark.parametrize(
    "total,success,expected_rate",
    [
        (100, 95, 95.0),
        (200, 200, 100.0),
        (50, 0, 0.0),
    ],
)
def test_success_rate_formula(total: int, success: int, expected_rate: float):
    rate = round(100.0 * success / total, 1) if total else 0.0
    assert rate == expected_rate


@pytest.mark.parametrize(
    "requests,total,expected_pct",
    [
        (75, 100, 75.0),
        (0, 100, 0.0),
        (100, 100, 100.0),
    ],
)
def test_percentage_formula(requests: int, total: int, expected_pct: float):
    pct = round(100.0 * requests / total, 1) if total else 0.0
    assert pct == expected_pct


# ---------------------------------------------------------------------------
# LatencyAnalytics
# ---------------------------------------------------------------------------


def test_latency_analytics_nullable_percentiles():
    la = LatencyAnalytics(
        data=[],
        avg_ms=0.0,
        p50_ms=None,
        p95_ms=None,
        by_provider={},
        period_days=30,
    )
    assert la.p50_ms is None
    assert la.p95_ms is None


def test_latency_analytics_with_data():
    la = LatencyAnalytics(
        data=[
            LatencyDataPoint(date="2025-01-01", avg_ms=820.0),
            LatencyDataPoint(date="2025-01-02", avg_ms=950.0),
        ],
        avg_ms=885.0,
        p50_ms=820.0,
        p95_ms=950.0,
        by_provider={"openai": 820.0, "anthropic": 950.0},
        period_days=7,
    )
    assert len(la.data) == 2
    assert la.p95_ms > la.p50_ms  # type: ignore[operator]
    assert "openai" in la.by_provider


# ---------------------------------------------------------------------------
# TokenAnalytics
# ---------------------------------------------------------------------------


def test_token_analytics_totals():
    ta = TokenAnalytics(
        total_tokens=1500,
        prompt_tokens=1000,
        completion_tokens=500,
        avg_per_request=150.0,
        period_days=30,
    )
    assert ta.total_tokens == ta.prompt_tokens + ta.completion_tokens
    assert ta.avg_per_request == 150.0


def test_token_analytics_zero():
    ta = TokenAnalytics(
        total_tokens=0,
        prompt_tokens=0,
        completion_tokens=0,
        avg_per_request=0.0,
        period_days=30,
    )
    assert ta.total_tokens == 0


# ---------------------------------------------------------------------------
# ConversationAnalytics
# ---------------------------------------------------------------------------


def test_conversation_analytics_zero():
    ca = ConversationAnalytics(
        total_conversations=0,
        avg_messages_per_conversation=0.0,
        period_days=30,
    )
    assert ca.avg_messages_per_conversation == 0.0


def test_conversation_avg_formula():
    total_conv = 10
    total_msgs = 37
    avg = round(total_msgs / total_conv, 1) if total_conv else 0.0
    assert avg == 3.7


# ---------------------------------------------------------------------------
# RoutingInsights
# ---------------------------------------------------------------------------


def test_routing_insights_empty_defaults():
    ri = RoutingInsights(
        strategy_distribution={},
        most_used_strategy="auto",
        most_selected_provider="—",
        period_days=30,
    )
    assert ri.most_used_strategy == "auto"


def test_routing_insights_strategy_distribution():
    dist = {"auto": 60, "cheapest": 25, "fastest": 10, "quality": 5}
    most_used = max(dist, key=lambda k: dist[k])
    assert most_used == "auto"


def test_provider_distribution_sorted():
    stats = [
        ProviderStat(provider="gemini", requests=10, percentage=10.0, cost=0.001, avg_latency_ms=650.0, success_rate=100.0),
        ProviderStat(provider="openai", requests=75, percentage=75.0, cost=0.05, avg_latency_ms=820.0, success_rate=98.7),
        ProviderStat(provider="anthropic", requests=15, percentage=15.0, cost=0.012, avg_latency_ms=1100.0, success_rate=96.0),
    ]
    sorted_stats = sorted(stats, key=lambda p: p.requests, reverse=True)
    assert sorted_stats[0].provider == "openai"
    assert sorted_stats[-1].provider == "gemini"

    pd = ProviderDistribution(providers=sorted_stats, period_days=30, total_requests=100)
    assert pd.total_requests == 100
