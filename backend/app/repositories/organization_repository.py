"""Organization repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """Data access layer for the organizations table."""

    model = Organization

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_slug(self, slug: str) -> Organization | None:
        """Return the organization with *slug*, or None."""
        result = await self._session.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        """Return True if *slug* is already taken."""
        result = await self._session.execute(
            select(Organization.id).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none() is not None

    async def create(self, *, name: str, slug: str) -> Organization:
        """Insert a new organization row."""
        from datetime import UTC, datetime
        org = Organization(
            name=name,
            slug=slug,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return await self.add(org)

    async def update_name(self, org: Organization, name: str) -> Organization:
        """Update the organization's display name."""
        from datetime import UTC, datetime
        org.name = name
        org.updated_at = datetime.now(UTC)
        await self._session.flush()
        return org
