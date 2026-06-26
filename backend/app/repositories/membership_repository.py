"""Membership repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.repositories.base import BaseRepository


class MembershipRepository(BaseRepository[Membership]):
    """Data access layer for the memberships table."""

    model = Membership

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_user_and_org(
        self, user_id: uuid.UUID, org_id: uuid.UUID
    ) -> Membership | None:
        """Return the membership for a specific user+org pair, or None."""
        result = await self._session.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.organization_id == org_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_orgs_for_user(
        self, user_id: uuid.UUID
    ) -> list[tuple[Membership, Organization]]:
        """Return all (Membership, Organization) pairs for *user_id*."""
        result = await self._session.execute(
            select(Membership, Organization)
            .join(Organization, Membership.organization_id == Organization.id)
            .where(Membership.user_id == user_id)
        )
        return list(result.tuples().all())

    async def get_members_of_org(
        self, org_id: uuid.UUID
    ) -> list[tuple[Membership, User]]:
        """Return all (Membership, User) pairs for *org_id*."""
        result = await self._session.execute(
            select(Membership, User)
            .join(User, Membership.user_id == User.id)
            .where(Membership.organization_id == org_id)
        )
        return list(result.tuples().all())

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        role: str,
    ) -> Membership:
        """Insert a new membership row."""
        from datetime import UTC, datetime
        membership = Membership(
            user_id=user_id,
            organization_id=org_id,
            role=role,
            created_at=datetime.now(UTC),
        )
        return await self.add(membership)

    async def update_role(self, membership: Membership, role: str) -> Membership:
        """Change the role on an existing membership."""
        membership.role = role
        await self._session.flush()
        return membership

    async def count_owners(self, org_id: uuid.UUID) -> int:
        """Count the number of OWNER memberships for *org_id*."""
        from sqlalchemy import func
        result = await self._session.execute(
            select(func.count(Membership.id)).where(
                Membership.organization_id == org_id,
                Membership.role == "owner",
            )
        )
        return result.scalar_one() or 0
