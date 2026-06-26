"""User repository — Phase 1 stub."""

from __future__ import annotations

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access for the users table."""

    model = User

    # TODO(phase-2): Add domain-specific queries:
    #   - get_by_email(email) -> User | None
    #   - get_active_users() -> list[User]
    #   - exists_by_email(email) -> bool
