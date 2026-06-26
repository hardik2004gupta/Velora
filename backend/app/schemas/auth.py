"""Authentication request / response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.common import VeloraBaseModel


class RegisterRequest(VeloraBaseModel):
    """Body for POST /auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(VeloraBaseModel):
    """Body for POST /auth/login."""

    email: EmailStr
    password: str


class TokenResponse(VeloraBaseModel):
    """Response body for POST /auth/login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(VeloraBaseModel):
    """Public user profile — returned from GET /auth/me."""

    id: uuid.UUID
    email: str
    full_name: str
    is_admin: bool
    created_at: datetime
