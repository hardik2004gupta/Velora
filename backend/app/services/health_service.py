"""Provider health check service — Phase 5."""

from __future__ import annotations

import time
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.provider_status import ProviderStatus
from app.providers.registry import get_registry
from app.schemas.provider import ProviderStatusResponse

log = get_logger(__name__)


class HealthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def check_all_providers(self) -> list[ProviderStatusResponse]:
        """Run live health checks for all registered providers and persist results."""
        registry = get_registry()
        results: list[ProviderStatusResponse] = []
        for provider in registry.get_all():
            result = await self._check_and_persist(provider)
            results.append(result)
        return results

    async def get_stored_status(self) -> list[ProviderStatusResponse]:
        """Return the last-known health status from DB without running new checks."""
        stmt = select(ProviderStatus).order_by(ProviderStatus.provider)
        rows = (await self._db.execute(stmt)).scalars().all()
        return [
            ProviderStatusResponse(
                provider=r.provider,
                status=r.status,
                latency_ms=r.latency_ms,
                avg_latency_ms=r.avg_latency_ms,
                uptime_percentage=(
                    float(r.uptime_percentage)
                    if r.uptime_percentage is not None
                    else None
                ),
                last_checked_at=r.last_checked_at,
                error_message=r.error_message,
            )
            for r in rows
        ]

    async def _check_and_persist(self, provider) -> ProviderStatusResponse:  # type: ignore[type-arg]
        pid = provider.get_id()
        start = time.monotonic()
        error_msg: str | None = None
        is_healthy = False

        try:
            is_healthy = await provider.health_check()
        except Exception as exc:
            error_msg = str(exc)
            log.warning("health_check_failed", provider=pid, error=error_msg)

        latency_ms = int((time.monotonic() - start) * 1_000)
        status = "healthy" if is_healthy else ("down" if error_msg else "degraded")
        now = datetime.now(UTC)

        # Upsert into provider_status table
        stmt = select(ProviderStatus).where(ProviderStatus.provider == pid)
        row = (await self._db.execute(stmt)).scalar_one_or_none()

        if row is None:
            row = ProviderStatus(
                provider=pid,
                status=status,
                latency_ms=latency_ms,
                avg_latency_ms=latency_ms,
                uptime_percentage=100.0 if is_healthy else 0.0,
                last_checked_at=now,
                error_message=error_msg,
                updated_at=now,
            )
            self._db.add(row)
        else:
            # Exponential moving average (weight 0.1 for new measurement)
            prev_avg = row.avg_latency_ms or latency_ms
            row.avg_latency_ms = int(prev_avg * 0.9 + latency_ms * 0.1)
            row.latency_ms = latency_ms
            row.status = status
            row.last_checked_at = now
            row.error_message = error_msg
            row.updated_at = now

        await self._db.flush()

        return ProviderStatusResponse(
            provider=pid,
            status=status,
            latency_ms=latency_ms,
            avg_latency_ms=row.avg_latency_ms,
            uptime_percentage=(
                float(row.uptime_percentage)
                if row.uptime_percentage is not None
                else None
            ),
            last_checked_at=now,
            error_message=error_msg,
        )
