"""Personal API key schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.common import VeloraBaseModel


class UserAPIKeyCreate(VeloraBaseModel):
    name: str = Field(min_length=1, max_length=100)


class UserAPIKeyResponse(VeloraBaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    last_used_at: datetime | None
    is_active: bool
    created_at: datetime


class UserAPIKeyCreateResponse(UserAPIKeyResponse):
    """Returned once at creation — includes the full key."""

    key: str
