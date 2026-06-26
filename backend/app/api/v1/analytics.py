"""Analytics endpoints — Phase 5."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.request_repository import RequestRepository
from app.schemas.analytics import (
    ConversationAnalytics,
    CostOverTime,
    DashboardOverview,
    LatencyAnalytics,
    ProviderDistribution,
    RoutingInsights,
    TokenAnalytics,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()

_PERIOD = Query(default=30, ge=1, le=365, description="Look-back window in days")


@router.get("/overview", response_model=DashboardOverview, summary="Dashboard summary cards")
async def overview(
    period_days: int = _PERIOD,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DashboardOverview:
    """Aggregated stats (requests, conversations, latency, cost) for the given period."""
    repo = RequestRepository(db)
    stats = await repo.get_overview_stats(user.id, period_days)
    return DashboardOverview(**stats)


@router.get("/cost", response_model=CostOverTime, summary="Daily cost series")
async def cost_analytics(
    period_days: int = _PERIOD,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CostOverTime:
    """Daily cost broken down by provider — suitable for a stacked area chart."""
    svc = AnalyticsService(db)
    return await svc.get_cost_over_time(user.id, period_days)


@router.get("/latency", response_model=LatencyAnalytics, summary="Latency analytics + P50/P95")
async def latency_analytics(
    period_days: int = _PERIOD,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> LatencyAnalytics:
    """Daily average latency, overall P50/P95, and per-provider breakdown."""
    svc = AnalyticsService(db)
    return await svc.get_latency_analytics(user.id, period_days)


@router.get("/providers", response_model=ProviderDistribution, summary="Provider usage distribution")
async def provider_distribution(
    period_days: int = _PERIOD,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ProviderDistribution:
    """Request count, cost, success rate, and latency per provider."""
    svc = AnalyticsService(db)
    return await svc.get_provider_distribution(user.id, period_days)


@router.get("/tokens", response_model=TokenAnalytics, summary="Token usage breakdown")
async def token_analytics(
    period_days: int = _PERIOD,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> TokenAnalytics:
    """Total, prompt, and completion token counts with per-request average."""
    svc = AnalyticsService(db)
    return await svc.get_token_analytics(user.id, period_days)


@router.get("/conversations", response_model=ConversationAnalytics, summary="Conversation analytics")
async def conversation_analytics(
    period_days: int = _PERIOD,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ConversationAnalytics:
    """Conversation count and average messages per conversation."""
    svc = AnalyticsService(db)
    return await svc.get_conversation_analytics(user.id, period_days)


@router.get("/routing", response_model=RoutingInsights, summary="Routing strategy insights")
async def routing_insights(
    period_days: int = _PERIOD,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RoutingInsights:
    """Strategy distribution, most-used strategy, and most-selected provider."""
    svc = AnalyticsService(db)
    return await svc.get_routing_insights(user.id, period_days)


# ---------------------------------------------------------------------------
# Legacy stub paths — redirect to new names for backward compatibility
# ---------------------------------------------------------------------------


@router.get("/cost-over-time", response_model=CostOverTime, include_in_schema=False)
async def cost_over_time_legacy(
    period_days: int = _PERIOD,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CostOverTime:
    return await cost_analytics(period_days, user, db)


@router.get("/latency-over-time", response_model=LatencyAnalytics, include_in_schema=False)
async def latency_over_time_legacy(
    period_days: int = _PERIOD,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> LatencyAnalytics:
    return await latency_analytics(period_days, user, db)


@router.get("/provider-distribution", response_model=ProviderDistribution, include_in_schema=False)
async def provider_distribution_legacy(
    period_days: int = _PERIOD,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ProviderDistribution:
    return await provider_distribution(period_days, user, db)
