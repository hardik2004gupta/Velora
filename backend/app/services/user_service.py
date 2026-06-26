"""User service — profile management and password changes."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.logging import get_logger
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import ChangePasswordRequest, UpdateUserProfileRequest, UserProfileResponse

log = get_logger(__name__)


class UserService:
    def __init__(self, db: AsyncSession, user_repo: UserRepository | None = None) -> None:
        self._db = db
        self._user_repo = user_repo or UserRepository(db)

    def get_profile(self, user: User) -> UserProfileResponse:
        return UserProfileResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_admin=user.is_admin,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def update_profile(
        self,
        user: User,
        payload: UpdateUserProfileRequest,
        *,
        request_id: str = "",
    ) -> User:
        if payload.full_name is not None:
            user = await self._user_repo.update_full_name(user, payload.full_name)
        log.info("user_profile_updated", user_id=str(user.id), request_id=request_id)
        return user

    async def change_password(
        self,
        user: User,
        payload: ChangePasswordRequest,
        *,
        request_id: str = "",
    ) -> None:
        if not verify_password(payload.current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect.")
        await self._user_repo.update_password(user, hash_password(payload.new_password))
        log.info("user_password_changed", user_id=str(user.id), request_id=request_id)
