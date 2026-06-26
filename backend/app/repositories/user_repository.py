"""User repository — all persistence logic for the users table."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access layer for the users table."""

    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_email(self, email: str) -> User | None:
        """Return the user with *email*, or None if not found."""
        result = await self._session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        """Return True if a user with *email* already exists."""
        result = await self._session.execute(
            select(User.id).where(User.email == email.lower())
        )
        return result.scalar_one_or_none() is not None

    async def get_active_by_id(self, user_id: uuid.UUID) -> User | None:
        """Return an active (not soft-deleted) user by primary key."""
        result = await self._session.execute(
            select(User).where(User.id == user_id, User.is_active == True)  # noqa: E712
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        email: str,
        hashed_password: str,
        full_name: str,
        is_verified: bool = False,
    ) -> User:
        """Insert a new user row and return it."""
        from datetime import UTC, datetime
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            is_verified=is_verified,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return await self.add(user)

    async def update_full_name(self, user: User, full_name: str) -> User:
        """Update the user's display name."""
        from datetime import UTC, datetime
        user.full_name = full_name
        user.updated_at = datetime.now(UTC)
        await self._session.flush()
        return user

    async def update_password(self, user: User, hashed_password: str) -> User:
        """Replace the user's password hash."""
        from datetime import UTC, datetime
        user.hashed_password = hashed_password
        user.updated_at = datetime.now(UTC)
        await self._session.flush()
        return user

    async def deactivate(self, user: User) -> User:
        """Soft-delete a user by clearing the is_active flag."""
        from datetime import UTC, datetime
        user.is_active = False
        user.updated_at = datetime.now(UTC)
        await self._session.flush()
        return user
