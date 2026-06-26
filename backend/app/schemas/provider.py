"""Provider status schemas."""

from __future__ import annotations

from datetime import datetime

from app.schemas.common import VeloraBaseModel


class ProviderStatusResponse(VeloraBaseModel):
    """Health snapshot for one provider."""

    provider: str
    status: str
    latency_ms: int | None
    avg_latency_ms: int | None
    uptime_percentage: float | None
    last_checked_at: datetime
    error_message: str | None = None


class ProvidersStatusResponse(VeloraBaseModel):
    """Response for GET /providers/status."""

    providers: list[ProviderStatusResponse]
