"""Provider listing and health endpoints — Phase 5."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.providers.registry import get_registry
from app.schemas.provider import (
    ModelInfo,
    ProviderInfo,
    ProvidersResponse,
    ProvidersStatusResponse,
)
from app.services.health_service import HealthService

router = APIRouter()

_DISPLAY_NAMES: dict[str, str] = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "gemini": "Google Gemini",
}


@router.get("", response_model=ProvidersResponse, summary="List providers with models and health")
async def list_providers(
    _user: User = Depends(get_current_user),
) -> ProvidersResponse:
    """Return all registered providers, their available models, and a live health status."""
    registry = get_registry()
    result: list[ProviderInfo] = []

    for provider in registry.get_all():
        pid = provider.get_id()
        is_healthy = await provider.health_check()
        models = [
            ModelInfo(
                id=m.model_id,
                context_window=m.context_window,
                quality_score=m.quality_score,
            )
            for m in provider.get_available_models()
        ]
        result.append(
            ProviderInfo(
                id=pid,
                name=_DISPLAY_NAMES.get(pid, pid.title()),
                status="healthy" if is_healthy else "down",
                models=models,
            )
        )

    return ProvidersResponse(providers=result)


@router.get(
    "/status",
    response_model=ProvidersStatusResponse,
    summary="Provider health detail with latency and uptime",
)
async def provider_status(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ProvidersStatusResponse:
    """
    Run a live health check against every registered provider, persist the result,
    and return status, measured latency, rolling-average latency, and last-checked
    timestamp for each.
    """
    svc = HealthService(db)
    results = await svc.check_all_providers()
    return ProvidersStatusResponse(providers=results)
