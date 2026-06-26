"""Analytics aggregation service — Phase 5."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request import Request
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


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _since(self, period_days: int) -> datetime:
        return datetime.now(UTC) - timedelta(days=period_days)

    async def get_cost_over_time(
        self, user_id: uuid.UUID, period_days: int = 30
    ) -> CostOverTime:
        since = self._since(period_days)
        where = and_(Request.user_id == user_id, Request.created_at >= since)

        stmt = (
            select(
                func.date(Request.created_at).label("date"),
                Request.provider,
                func.sum(Request.cost_usd).label("cost"),
            )
            .where(where)
            .group_by(func.date(Request.created_at), Request.provider)
            .order_by(func.date(Request.created_at))
        )
        rows = (await self._db.execute(stmt)).all()

        # Accumulate: date → provider → cost
        date_map: dict[str, dict[str, float]] = {}
        for row in rows:
            d = str(row.date)
            if d not in date_map:
                date_map[d] = {}
            date_map[d][row.provider] = float(row.cost or 0)

        data = [
            CostDataPoint(
                date=d,
                cost=sum(v.values()),
                openai=v.get("openai", 0.0),
                anthropic=v.get("anthropic", 0.0),
                gemini=v.get("gemini", 0.0),
            )
            for d, v in sorted(date_map.items())
        ]
        total = sum(p.cost for p in data)
        return CostOverTime(data=data, period_days=period_days, total=total)

    async def get_latency_analytics(
        self, user_id: uuid.UUID, period_days: int = 30
    ) -> LatencyAnalytics:
        since = self._since(period_days)
        where = and_(
            Request.user_id == user_id,
            Request.created_at >= since,
            Request.latency_ms.is_not(None),
        )

        # Daily averages for chart
        daily_stmt = (
            select(
                func.date(Request.created_at).label("date"),
                func.avg(Request.latency_ms).label("avg_ms"),
            )
            .where(where)
            .group_by(func.date(Request.created_at))
            .order_by(func.date(Request.created_at))
        )
        daily_rows = (await self._db.execute(daily_stmt)).all()
        data = [
            LatencyDataPoint(date=str(r.date), avg_ms=float(r.avg_ms or 0))
            for r in daily_rows
        ]

        # Overall stats: avg + P50 + P95
        perc_stmt = select(
            func.avg(Request.latency_ms).label("avg_ms"),
            func.percentile_cont(0.5)
            .within_group(Request.latency_ms.asc())
            .label("p50"),
            func.percentile_cont(0.95)
            .within_group(Request.latency_ms.asc())
            .label("p95"),
        ).where(where)
        perc_row = (await self._db.execute(perc_stmt)).one()

        # Per-provider averages
        by_prov_stmt = (
            select(
                Request.provider,
                func.avg(Request.latency_ms).label("avg_ms"),
            )
            .where(where)
            .group_by(Request.provider)
        )
        by_prov_rows = (await self._db.execute(by_prov_stmt)).all()
        by_provider = {r.provider: float(r.avg_ms or 0) for r in by_prov_rows}

        return LatencyAnalytics(
            data=data,
            avg_ms=float(perc_row.avg_ms or 0),
            p50_ms=float(perc_row.p50) if perc_row.p50 is not None else None,
            p95_ms=float(perc_row.p95) if perc_row.p95 is not None else None,
            by_provider=by_provider,
            period_days=period_days,
        )

    async def get_provider_distribution(
        self, user_id: uuid.UUID, period_days: int = 30
    ) -> ProviderDistribution:
        since = self._since(period_days)
        where = and_(Request.user_id == user_id, Request.created_at >= since)

        stmt = (
            select(
                Request.provider,
                func.count(Request.id).label("requests"),
                func.sum(Request.cost_usd).label("cost"),
                func.avg(Request.latency_ms).label("avg_latency_ms"),
                func.sum(
                    case((Request.status == "success", 1), else_=0)
                ).label("success_count"),
            )
            .where(where)
            .group_by(Request.provider)
        )
        rows = (await self._db.execute(stmt)).all()

        total = sum(int(r.requests) for r in rows)
        providers = [
            ProviderStat(
                provider=r.provider,
                requests=int(r.requests),
                percentage=round(100.0 * int(r.requests) / total, 1) if total else 0.0,
                cost=float(r.cost or 0),
                avg_latency_ms=(
                    float(r.avg_latency_ms) if r.avg_latency_ms is not None else None
                ),
                success_rate=(
                    round(100.0 * int(r.success_count) / int(r.requests), 1)
                    if int(r.requests)
                    else 0.0
                ),
            )
            for r in rows
        ]
        return ProviderDistribution(
            providers=sorted(providers, key=lambda p: p.requests, reverse=True),
            period_days=period_days,
            total_requests=total,
        )

    async def get_token_analytics(
        self, user_id: uuid.UUID, period_days: int = 30
    ) -> TokenAnalytics:
        since = self._since(period_days)
        where = and_(Request.user_id == user_id, Request.created_at >= since)

        stmt = select(
            func.coalesce(func.sum(Request.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(Request.prompt_tokens), 0).label("prompt_tokens"),
            func.coalesce(func.sum(Request.completion_tokens), 0).label(
                "completion_tokens"
            ),
            func.coalesce(func.avg(Request.total_tokens), 0).label("avg_per_request"),
        ).where(where)
        row = (await self._db.execute(stmt)).one()

        return TokenAnalytics(
            total_tokens=int(row.total_tokens),
            prompt_tokens=int(row.prompt_tokens),
            completion_tokens=int(row.completion_tokens),
            avg_per_request=round(float(row.avg_per_request or 0), 1),
            period_days=period_days,
        )

    async def get_conversation_analytics(
        self, user_id: uuid.UUID, period_days: int = 30
    ) -> ConversationAnalytics:
        since = self._since(period_days)
        where = and_(
            Request.user_id == user_id,
            Request.created_at >= since,
            Request.conversation_id.is_not(None),
        )

        stmt = select(
            func.count(distinct(Request.conversation_id)).label(
                "total_conversations"
            ),
            func.count(Request.id).label("total_messages"),
        ).where(where)
        row = (await self._db.execute(stmt)).one()

        total_conv = int(row.total_conversations)
        total_msgs = int(row.total_messages)
        avg = round(total_msgs / total_conv, 1) if total_conv else 0.0

        return ConversationAnalytics(
            total_conversations=total_conv,
            avg_messages_per_conversation=avg,
            period_days=period_days,
        )

    async def get_routing_insights(
        self, user_id: uuid.UUID, period_days: int = 30
    ) -> RoutingInsights:
        since = self._since(period_days)
        where = and_(Request.user_id == user_id, Request.created_at >= since)

        # Strategy distribution
        strat_stmt = (
            select(
                Request.routing_strategy,
                func.count(Request.id).label("count"),
            )
            .where(where)
            .group_by(Request.routing_strategy)
        )
        strat_rows = (await self._db.execute(strat_stmt)).all()
        strategy_dist = {r.routing_strategy: int(r.count) for r in strat_rows}
        most_used = (
            max(strategy_dist, key=lambda k: strategy_dist[k])
            if strategy_dist
            else "auto"
        )

        # Most-selected provider
        prov_stmt = (
            select(Request.provider, func.count(Request.id).label("count"))
            .where(where)
            .group_by(Request.provider)
            .order_by(func.count(Request.id).desc())
            .limit(1)
        )
        prov_row = (await self._db.execute(prov_stmt)).first()
        most_provider = prov_row.provider if prov_row else "—"

        return RoutingInsights(
            strategy_distribution=strategy_dist,
            most_used_strategy=most_used,
            most_selected_provider=most_provider,
            period_days=period_days,
        )
