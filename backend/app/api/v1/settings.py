"""User settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.settings import UpdateSettingsRequest, UserSettingsResponse
from app.services.settings_service import SettingsService

router = APIRouter()


@router.get("", response_model=UserSettingsResponse, summary="Get current user settings")
async def get_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserSettingsResponse:
    service = SettingsService(db)
    settings = await service.get(user)
    return UserSettingsResponse(
        default_routing_strategy=settings.default_routing_strategy,
        default_model=settings.default_model,
        theme=settings.theme,
        max_tokens=settings.max_tokens,
        temperature=float(settings.temperature),
    )


@router.patch("", response_model=UserSettingsResponse, summary="Update user settings")
async def update_settings(
    payload: UpdateSettingsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserSettingsResponse:
    service = SettingsService(db)
    settings = await service.update(user, payload)
    return UserSettingsResponse(
        default_routing_strategy=settings.default_routing_strategy,
        default_model=settings.default_model,
        theme=settings.theme,
        max_tokens=settings.max_tokens,
        temperature=float(settings.temperature),
    )
