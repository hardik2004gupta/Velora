"""Cache management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.cache import CacheClearResponse, CacheStats
from app.services.cache_service import CacheService

router = APIRouter()


@router.get("/stats", response_model=CacheStats, summary="Prompt cache statistics")
async def cache_stats(
    _user: User = Depends(get_current_user),
) -> CacheStats:
    svc = CacheService()
    data = await svc.get_stats()
    return CacheStats(**data)


@router.post("/clear", response_model=CacheClearResponse, summary="Clear all cached prompts")
async def clear_cache(
    _user: User = Depends(get_current_user),
) -> CacheClearResponse:
    svc = CacheService()
    cleared = await svc.clear()
    return CacheClearResponse(
        cleared=cleared,
        message=f"Cleared {cleared} cached prompt(s).",
    )
