"""API key repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey
from app.repositories.base import BaseRepository


class APIKeyRepository(BaseRepository[APIKey]):
    """Data access layer for the api_keys table."""

    model = APIKey

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_active_by_org(self, org_id: uuid.UUID) -> list[APIKey]:
        """Return all non-revoked keys for *org_id*."""
        result = await self._session.execute(
            select(APIKey).where(
                APIKey.organization_id == org_id,
                APIKey.revoked == False,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def get_by_prefix(self, prefix: str) -> list[APIKey]:
        """
        Return all non-revoked, non-expired keys matching *prefix*.

        The prefix-based lookup reduces the bcrypt verification set to ≤ 1 row
        under normal operation.
        """
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(APIKey).where(
                APIKey.key_prefix == prefix,
                APIKey.revoked == False,  # noqa: E712
            )
        )
        keys = list(result.scalars().all())
        # Filter expired in Python (avoids NULL comparison edge cases)
        return [k for k in keys if k.expires_at is None or k.expires_at > now]

    async def create(
        self,
        *,
        org_id: uuid.UUID,
        name: str,
        key_prefix: str,
        hashed_key: str,
        role: str,
        expires_at: datetime | None,
    ) -> APIKey:
        """Insert a new API key row."""
        key = APIKey(
            organization_id=org_id,
            name=name,
            key_prefix=key_prefix,
            hashed_key=hashed_key,
            role=role,
            expires_at=expires_at,
            revoked=False,
            created_at=datetime.now(UTC),
        )
        return await self.add(key)

    async def revoke(self, api_key: APIKey) -> APIKey:
        """Mark *api_key* as revoked (soft delete for audit trail)."""
        api_key.revoked = True
        await self._session.flush()
        return api_key

    async def touch(self, api_key: APIKey) -> None:
        """Update ``last_used_at`` to now."""
        api_key.last_used_at = datetime.now(UTC)
        await self._session.flush()
