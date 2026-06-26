"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenPairResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", status_code=201, response_model=RegisterResponse, summary="Register a new account")
async def register(
    payload: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> RegisterResponse:
    service = AuthService(db)
    user, tokens = await service.register(
        payload,
        request_id=request.state.request_id if hasattr(request.state, "request_id") else "",
    )
    return RegisterResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_admin=user.is_admin,
            is_verified=user.is_verified,
            created_at=user.created_at,
        ),
        tokens=tokens,
    )


@router.post("/login", response_model=TokenPairResponse, summary="Login and receive tokens")
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> TokenPairResponse:
    service = AuthService(db)
    _, tokens = await service.login(
        payload.email,
        payload.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        request_id=request.state.request_id if hasattr(request.state, "request_id") else "",
    )
    return tokens


@router.post("/refresh", response_model=TokenPairResponse, summary="Rotate refresh token")
async def refresh(
    payload: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> TokenPairResponse:
    service = AuthService(db)
    return await service.refresh(
        payload.refresh_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        request_id=request.state.request_id if hasattr(request.state, "request_id") else "",
    )


@router.post("/logout", response_model=LogoutResponse, summary="Invalidate refresh token")
async def logout(
    payload: LogoutRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> LogoutResponse:
    service = AuthService(db)
    await service.logout(
        payload.refresh_token,
        user_id=str(user.id),
        request_id=request.state.request_id if hasattr(request.state, "request_id") else "",
    )
    return LogoutResponse()


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_admin=user.is_admin,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )
