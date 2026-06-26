"""Request repository — database access for the requests table."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request import Request


class RequestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_request_id(
        self, request_id: str, user_id: uuid.UUID
    ) -> Request | None:
        """Fetch a single request by human-readable request_id or UUID, scoped to user."""
        maybe_uuid = _try_uuid(request_id)

        if maybe_uuid is not None:
            id_filter = or_(
                Request.request_id == request_id,
                Request.id == maybe_uuid,
            )
        else:
            id_filter = Request.request_id == request_id

        stmt = select(Request).where(and_(id_filter, Request.user_id == user_id))
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        page: int = 1,
        limit: int = 20,
        provider: str | None = None,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> tuple[list[Request], int]:
        """Return a paginated list and total count for one user."""
        filters: list[Any] = [Request.user_id == user_id]

        if provider:
            filters.append(Request.provider == provider)
        if status:
            filters.append(Request.status == status)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    Request.request_id.ilike(pattern),
                    Request.prompt.ilike(pattern),
                    Request.provider.ilike(pattern),
                )
            )

        where_clause = and_(*filters)

        count_stmt = select(func.count(Request.id)).where(where_clause)
        total: int = (await self._db.execute(count_stmt)).scalar_one()

        sort_col = {
            "created_at": Request.created_at,
            "latency_ms": Request.latency_ms,
            "cost_usd": Request.cost_usd,
            "provider": Request.provider,
        }.get(sort_by, Request.created_at)

        order = desc(sort_col) if sort_dir == "desc" else sort_col
        offset = (page - 1) * limit

        stmt = (
            select(Request)
            .where(where_clause)
            .order_by(order)
            .offset(offset)
            .limit(limit)
        )
        rows = (await self._db.execute(stmt)).scalars().all()
        return list(rows), total

    async def list_all_for_export(
        self,
        user_id: uuid.UUID,
        provider: str | None = None,
        status: str | None = None,
    ) -> list[Request]:
        """Return all user records for CSV/JSON export (no pagination)."""
        filters: list[Any] = [Request.user_id == user_id]
        if provider:
            filters.append(Request.provider == provider)
        if status:
            filters.append(Request.status == status)

        stmt = (
            select(Request)
            .where(and_(*filters))
            .order_by(desc(Request.created_at))
        )
        return list((await self._db.execute(stmt)).scalars().all())

    async def get_overview_stats(
        self, user_id: uuid.UUID, period_days: int = 30
    ) -> dict:
        """Aggregate dashboard stats for one user over the given period."""
        since = datetime.now(UTC) - timedelta(days=period_days)
        where = and_(Request.user_id == user_id, Request.created_at >= since)

        stmt = select(
            func.count(Request.id).label("total_requests"),
            func.count(func.distinct(Request.conversation_id)).label("total_conversations"),
            func.coalesce(func.avg(Request.latency_ms), 0).label("avg_latency_ms"),
            func.coalesce(func.sum(Request.cost_usd), 0).label("total_cost_usd"),
        ).where(where)

        row = (await self._db.execute(stmt)).one()
        return {
            "total_requests": int(row.total_requests),
            "total_conversations": int(row.total_conversations),
            "avg_latency_ms": float(row.avg_latency_ms or 0),
            "total_cost_usd": float(row.total_cost_usd or 0),
            "period_days": period_days,
        }


def _try_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        return None
