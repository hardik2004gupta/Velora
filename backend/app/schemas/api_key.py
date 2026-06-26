"""API key schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.common import VeloraBaseModel


class CreateAPIKeyRequest(VeloraBaseModel):
    """Body for POST /api-keys."""

    name: str = Field(min_length=1, max_length=100)
    expires_at: datetime | None = None


class APIKeyCreatedResponse(VeloraBaseModel):
    """Response for POST /api-keys — includes the full key (shown once only)."""

    id: uuid.UUID
    name: str
    key: str
    key_prefix: str
    expires_at: datetime | None
    created_at: datetime


class APIKeyResponse(VeloraBaseModel):
    """Safe API key representation — key value is never included."""

    id: uuid.UUID
    name: str
    key_prefix: str
    last_used_at: datetime | None
    expires_at: datetime | None
    is_active: bool
    created_at: datetime


class APIKeysListResponse(VeloraBaseModel):
    """Response for GET /api-keys."""

    items: list[APIKeyResponse]
    total: int
