"""Provider listing and health endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.providers.registry import get_registry
from app.schemas.provider import ModelInfo, ProviderInfo, ProvidersResponse

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
    """Return all registered providers, their available models, and live health status."""
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


# Phase 3+ stub — kept for the router registration
@router.get("/status", summary="Provider health detail (Phase 3+)")
async def provider_status_detail() -> dict:
    return {"message": "Detailed health metrics are implemented in Phase 3."}
