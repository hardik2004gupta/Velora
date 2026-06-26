"""Repository for the user_settings table."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_settings import UserSettings
from app.repositories.base import BaseRepository


class UserSettingsRepository(BaseRepository[UserSettings]):
    model = UserSettings

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_user_id(self, user_id: uuid.UUID) -> UserSettings | None:
        result = await self._session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: uuid.UUID, **fields: object) -> UserSettings:
        """Create or update settings for *user_id*."""
        settings = await self.get_by_user_id(user_id)
        if settings is None:
            settings = UserSettings(
                user_id=user_id,
                updated_at=datetime.now(UTC),
                **fields,
            )
            return await self.add(settings)

        for key, value in fields.items():
            setattr(settings, key, value)
        settings.updated_at = datetime.now(UTC)
        await self._session.flush()
        return settings
