"""User profile endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, UpdateUserProfileRequest, UserProfileResponse
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse, summary="Get current user profile")
async def get_me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserProfileResponse:
    service = UserService(db)
    return service.get_profile(user)


@router.patch("/me", response_model=UserProfileResponse, summary="Update current user profile")
async def update_me(
    payload: UpdateUserProfileRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserProfileResponse:
    service = UserService(db)
    updated_user = await service.update_profile(
        user, payload, request_id=getattr(request.state, "request_id", "")
    )
    return service.get_profile(updated_user)


@router.post("/me/password", status_code=204, summary="Change current user password")
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    service = UserService(db)
    await service.change_password(
        user, payload, request_id=getattr(request.state, "request_id", "")
    )
