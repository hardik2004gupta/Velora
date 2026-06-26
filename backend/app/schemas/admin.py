"""Admin dashboard schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.schemas.common import VeloraBaseModel


class AdminUserRow(VeloraBaseModel):
    """User row in the admin users table."""

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    total_requests: int
    total_cost_usd: float


class AdminUsersResponse(VeloraBaseModel):
    """Response for GET /admin/users."""

    items: list[AdminUserRow]
    total: int


class AdminStatsResponse(VeloraBaseModel):
    """Response for GET /admin/stats."""

    total_users: int
    total_requests: int
    total_cost_usd: float
    active_providers: int
    requests_today: int


class UpdateUserStatusRequest(VeloraBaseModel):
    """Body for PATCH /admin/users/{id}/status."""

    is_active: bool
