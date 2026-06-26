"""Provider info and health schemas."""

from __future__ import annotations

from datetime import datetime

from app.schemas.common import VeloraBaseModel


class ModelInfo(VeloraBaseModel):
    """Metadata for a single model offered by a provider."""

    id: str
    context_window: int
    quality_score: float


class ProviderInfo(VeloraBaseModel):
    """Summary of one provider's identity, health, and available models."""

    id: str
    name: str
    status: str  # healthy | down
    models: list[ModelInfo]


class ProvidersResponse(VeloraBaseModel):
    """Response for GET /providers."""

    providers: list[ProviderInfo]


# ---------------------------------------------------------------------------
# Phase 3+ — provider health with latency / uptime (kept for forward compat)
# ---------------------------------------------------------------------------


class ProviderStatusResponse(VeloraBaseModel):
    """Health snapshot for one provider (Phase 3+)."""

    provider: str
    status: str
    latency_ms: int | None
    avg_latency_ms: int | None
    uptime_percentage: float | None
    last_checked_at: datetime
    error_message: str | None = None


class ProvidersStatusResponse(VeloraBaseModel):
    """Response for GET /providers/status (Phase 3+)."""

    providers: list[ProviderStatusResponse]
