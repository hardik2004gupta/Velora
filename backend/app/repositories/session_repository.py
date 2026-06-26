"""Session repository — refresh token persistence."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[Session]):
    """Data access layer for the sessions table."""

    model = Session

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_token_hash(self, token_hash: str) -> Session | None:
        """
        Return the session matching *token_hash*, or None.

        Only returns sessions that have not yet expired.
        """
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(Session).where(
                Session.refresh_token_hash == token_hash,
                Session.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: uuid.UUID) -> list[Session]:
        """Return all active sessions for *user_id*."""
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(Session).where(
                Session.user_id == user_id,
                Session.expires_at > now,
            )
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        refresh_token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> Session:
        """Insert a new session row."""
        sess = Session(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
            created_at=datetime.now(UTC),
        )
        return await self.add(sess)

    async def delete_by_token_hash(self, token_hash: str) -> bool:
        """
        Delete the session with *token_hash*.

        Returns True if a session was deleted, False if none matched.
        """
        sess = await self.get_by_token_hash(token_hash)
        if sess is None:
            return False
        await self.delete(sess)
        return True

    async def delete_all_for_user(self, user_id: uuid.UUID) -> int:
        """
        Delete ALL sessions for *user_id* (force logout everywhere).

        Returns the number of sessions deleted.
        """
        sessions = await self.get_by_user(user_id)
        for sess in sessions:
            await self.delete(sess)
        return len(sessions)
