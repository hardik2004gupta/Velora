"""Personal (user-scoped) API key service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.security import (
    generate_api_key,
    get_api_key_prefix,
    hash_api_key,
    verify_api_key,
)
from app.models.user import User
from app.models.user_api_key import UserAPIKey
from app.repositories.user_repository import UserRepository


class UserKeyService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_for_user(self, user_id: uuid.UUID) -> list[UserAPIKey]:
        result = await self._db.execute(
            select(UserAPIKey)
            .where(UserAPIKey.user_id == user_id, UserAPIKey.is_active == True)  # noqa: E712
            .order_by(UserAPIKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, user_id: uuid.UUID, name: str) -> tuple[UserAPIKey, str]:
        """Create a personal API key. Returns (model, plain_key) — plain_key shown once."""
        plain_key = generate_api_key()
        prefix = get_api_key_prefix(plain_key)
        hashed = hash_api_key(plain_key)

        key = UserAPIKey(
            id=uuid.uuid4(),
            user_id=user_id,
            name=name,
            key_prefix=prefix,
            hashed_key=hashed,
            is_active=True,
            created_at=datetime.now(UTC),
        )
        self._db.add(key)
        await self._db.flush()
        return key, plain_key

    async def revoke(self, key_id: uuid.UUID, user_id: uuid.UUID) -> None:
        result = await self._db.execute(
            select(UserAPIKey).where(
                UserAPIKey.id == key_id,
                UserAPIKey.user_id == user_id,
                UserAPIKey.is_active == True,  # noqa: E712
            )
        )
        key = result.scalar_one_or_none()
        if key is None:
            raise NotFoundError("API key not found.")
        key.is_active = False
        await self._db.flush()

    async def verify_and_get_user(self, plain_key: str) -> User:
        """Verify an X-API-Key header value and return the associated user."""
        prefix = get_api_key_prefix(plain_key)
        result = await self._db.execute(
            select(UserAPIKey).where(
                UserAPIKey.key_prefix == prefix,
                UserAPIKey.is_active == True,  # noqa: E712
            )
        )
        candidates = list(result.scalars().all())

        matched: UserAPIKey | None = None
        for candidate in candidates:
            if verify_api_key(plain_key, candidate.hashed_key):
                matched = candidate
                break

        if matched is None:
            raise AuthenticationError("Invalid API key.")

        # Update last_used_at (best-effort)
        await self._db.execute(
            update(UserAPIKey)
            .where(UserAPIKey.id == matched.id)
            .values(last_used_at=datetime.now(UTC))
        )

        user_repo = UserRepository(self._db)
        user = await user_repo.get_active_by_id(matched.user_id)
        if user is None:
            raise AuthenticationError("User account not found or disabled.")
        return user
