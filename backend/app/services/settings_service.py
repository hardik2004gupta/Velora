"""User settings service — get and update per-user preferences."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_settings import UserSettings
from app.repositories.user_settings_repository import UserSettingsRepository
from app.schemas.settings import UpdateSettingsRequest


class SettingsService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = UserSettingsRepository(db)

    async def get(self, user: User) -> UserSettings:
        """Return the user's settings, or a default object if none exist yet."""
        settings = await self._repo.get_by_user_id(user.id)
        if settings is None:
            # Return in-memory defaults — not persisted until first PATCH
            return UserSettings(
                user_id=user.id,
                default_routing_strategy="auto",
                default_model=None,
                theme="dark",
                max_tokens=2048,
                temperature=0.70,
                updated_at=datetime.now(UTC),
            )
        return settings

    async def update(self, user: User, payload: UpdateSettingsRequest) -> UserSettings:
        """Upsert settings fields from *payload* (None fields are skipped)."""
        updates = {k: v for k, v in payload.model_dump().items() if v is not None}
        return await self._repo.upsert(user.id, **updates)
