"""
Authentication dependencies.

Injected into protected route handlers via FastAPI's ``Depends()``.

Usage::

    from app.dependencies.auth import get_current_user, get_current_admin_user

    @router.get("/protected")
    async def protected_route(user = Depends(get_current_user)):
        ...
"""

from __future__ import annotations

import uuid

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AdminRequiredError, AuthenticationError
from app.core.security import extract_subject
from app.database.session import get_db_session
from app.models.user import User
from app.repositories.user_repository import UserRepository

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> str:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Authorization header is missing or invalid.")
    return credentials.credentials


async def get_current_user(
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Validate the JWT and load the full User ORM object from the database.

    Raises:
        AuthenticationError: If the token is invalid/expired or the user
            no longer exists or is inactive.
    """
    user_id_str = extract_subject(token)
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationError("Token subject is not a valid user ID.")

    user_repo = UserRepository(db)
    user = await user_repo.get_active_by_id(user_id)
    if user is None:
        raise AuthenticationError("User account not found or has been disabled.")
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User | None:
    """Return the authenticated user or None if no token is provided."""
    if credentials is None or not credentials.credentials:
        return None
    try:
        user_id_str = extract_subject(credentials.credentials)
        user_id = uuid.UUID(user_id_str)
        user_repo = UserRepository(db)
        return await user_repo.get_active_by_id(user_id)
    except Exception:
        return None


async def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    """Assert the authenticated user has admin privileges."""
    if not user.is_admin:
        raise AdminRequiredError("Admin access is required.")
    return user
