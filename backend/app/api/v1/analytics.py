"""Analytics endpoints — Phase 4."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.request_repository import RequestRepository
from app.schemas.analytics import DashboardOverview

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview, summary="Dashboard summary stats")
async def overview(
    period_days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DashboardOverview:
    """
    Return aggregated stats for the dashboard summary cards.

    Counts requests, unique conversations, average latency, and total cost
    over the requested period (default: last 30 days).
    """
    repo = RequestRepository(db)
    stats = await repo.get_overview_stats(user.id, period_days)
    return DashboardOverview(**stats)


@router.get("/cost-over-time", summary="Daily cost series (Phase 5+)")
async def cost_over_time() -> dict:
    return {"message": "Full analytics charts implemented in Phase 5."}


@router.get("/latency-over-time", summary="Latency by provider over time (Phase 5+)")
async def latency_over_time() -> dict:
    return {"message": "Full analytics charts implemented in Phase 5."}


@router.get("/provider-distribution", summary="Provider usage breakdown (Phase 5+)")
async def provider_distribution() -> dict:
    return {"message": "Full analytics charts implemented in Phase 5."}
