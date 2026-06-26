"""Authentication request / response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.common import VeloraBaseModel


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RegisterRequest(VeloraBaseModel):
    """Body for POST /auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(VeloraBaseModel):
    """Body for POST /auth/login."""

    email: EmailStr
    password: str


class RefreshRequest(VeloraBaseModel):
    """Body for POST /auth/refresh."""

    refresh_token: str


class LogoutRequest(VeloraBaseModel):
    """Body for POST /auth/logout."""

    refresh_token: str


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TokenPairResponse(VeloraBaseModel):
    """Token pair issued on login or refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token TTL in seconds


class UserResponse(VeloraBaseModel):
    """Public user profile — returned from GET /auth/me."""

    id: uuid.UUID
    email: str
    full_name: str
    is_admin: bool
    is_verified: bool
    created_at: datetime


class RegisterResponse(VeloraBaseModel):
    """Response body for POST /auth/register."""

    user: UserResponse
    tokens: TokenPairResponse


class LogoutResponse(VeloraBaseModel):
    """Response body for POST /auth/logout."""

    message: str = "Logged out successfully."
