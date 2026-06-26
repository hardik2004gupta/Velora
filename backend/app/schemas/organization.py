"""Organization and membership schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from app.core.rbac import Role
from app.schemas.common import VeloraBaseModel


# ---------------------------------------------------------------------------
# Organization schemas
# ---------------------------------------------------------------------------


class CreateOrganizationRequest(VeloraBaseModel):
    """Body for POST /organizations."""

    name: str = Field(min_length=1, max_length=255)


class UpdateOrganizationRequest(VeloraBaseModel):
    """Body for PATCH /organizations/{id}."""

    name: str | None = Field(default=None, min_length=1, max_length=255)


class OrganizationResponse(VeloraBaseModel):
    """Public organization representation."""

    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime


class OrganizationWithRoleResponse(OrganizationResponse):
    """Organization + the requesting user's role within it."""

    role: str


class OrganizationsListResponse(VeloraBaseModel):
    """Response for GET /organizations."""

    items: list[OrganizationWithRoleResponse]
    total: int


# ---------------------------------------------------------------------------
# Membership schemas
# ---------------------------------------------------------------------------


class MemberResponse(VeloraBaseModel):
    """A single member of an organization."""

    user_id: uuid.UUID
    email: str
    full_name: str
    role: str
    joined_at: datetime


class InviteMemberRequest(VeloraBaseModel):
    """Body for POST /organizations/{id}/members."""

    email: str
    role: Role = Role.DEVELOPER


class UpdateMemberRoleRequest(VeloraBaseModel):
    """Body for PATCH /organizations/{id}/members/{user_id}."""

    role: Role
