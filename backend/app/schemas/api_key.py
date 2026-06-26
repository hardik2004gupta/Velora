"""API key schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from app.core.rbac import Role
from app.schemas.common import VeloraBaseModel


class CreateAPIKeyRequest(VeloraBaseModel):
    """Body for POST /api-keys."""

    name: str = Field(min_length=1, max_length=100)
    role: Role = Role.DEVELOPER
    expires_in_days: int | None = Field(default=None, ge=1, le=3650)


class CreateAPIKeyResponse(VeloraBaseModel):
    """
    Response for POST /api-keys.

    ``full_key`` contains the plaintext API key — shown ONCE only.
    The client must store it securely immediately.
    """

    id: str
    name: str
    full_key: str
    key_prefix: str
    role: str
    expires_at: datetime | None
    created_at: datetime


class APIKeyResponse(VeloraBaseModel):
    """Safe API key representation — the key value is never included."""

    id: uuid.UUID
    name: str
    key_prefix: str
    role: str
    last_used_at: datetime | None
    expires_at: datetime | None
    revoked: bool
    is_active: bool
    created_at: datetime


class APIKeysListResponse(VeloraBaseModel):
    """Response for GET /api-keys."""

    items: list[APIKeyResponse]
    total: int


class RotateAPIKeyResponse(VeloraBaseModel):
    """
    Response for POST /api-keys/{id}/rotate.

    ``new_key`` contains the full plaintext replacement key.
    The old key is immediately revoked.
    """

    id: str
    name: str
    new_key: str
    key_prefix: str
    role: str
    expires_at: datetime | None
    created_at: datetime
