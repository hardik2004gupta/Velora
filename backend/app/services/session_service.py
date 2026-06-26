"""Session service — thin wrapper around SessionRepository for session management UI."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.repositories.session_repository import SessionRepository


class SessionService:
    def __init__(
        self,
        db: AsyncSession,
        session_repo: SessionRepository | None = None,
    ) -> None:
        self._repo = session_repo or SessionRepository(db)

    async def list_for_user(self, user_id: uuid.UUID) -> list[Session]:
        return await self._repo.get_by_user(user_id)

    async def revoke_all(self, user_id: uuid.UUID) -> int:
        """Revoke all sessions (force logout from all devices). Returns count."""
        return await self._repo.delete_all_for_user(user_id)
