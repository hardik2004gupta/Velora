"""User profile schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.common import VeloraBaseModel


class UserProfileResponse(VeloraBaseModel):
    """Full user profile returned from GET /users/me."""

    id: uuid.UUID
    email: str
    full_name: str
    is_admin: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class UpdateUserProfileRequest(VeloraBaseModel):
    """Body for PATCH /users/me."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)


class ChangePasswordRequest(VeloraBaseModel):
    """Body for POST /users/me/password."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
