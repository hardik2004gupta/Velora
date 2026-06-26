"""
Authentication dependencies.

These are injected into protected route handlers via FastAPI's ``Depends()``.

Usage::

    from app.dependencies.auth import get_current_user, get_current_admin_user

    @router.get("/protected")
    async def protected_route(user = Depends(get_current_user)):
        return {"user_id": str(user.id)}
"""

from __future__ import annotations

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AdminRequiredError, AuthenticationError
from app.core.security import extract_subject

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> str:
    """
    Extract and return the raw Bearer token from the Authorization header.

    Raises:
        AuthenticationError: If no Authorization header is present.
    """
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Authorization header is missing or invalid.")
    return credentials.credentials


async def get_current_user_id(token: str = Depends(get_token)) -> str:
    """
    Validate the JWT token and return the authenticated user's ID string.

    This is the foundation dependency.  Business logic routes that need the
    full ``User`` ORM object should build on top of this in Phase 2.

    Raises:
        AuthenticationError / ExpiredTokenError / InvalidTokenError
    """
    return extract_subject(token)


# ---------------------------------------------------------------------------
# Placeholder for Phase 2 — will load the full User ORM object from DB
# ---------------------------------------------------------------------------


async def get_current_user(user_id: str = Depends(get_current_user_id)) -> str:
    """
    Return the authenticated user.

    Phase 1: Returns just the user ID string.
    Phase 2: Will query the DB and return a ``User`` ORM instance.
    """
    # TODO(phase-2): Load User from database using user_id
    return user_id


async def get_current_admin_user(user_id: str = Depends(get_current_user)) -> str:
    """
    Return the authenticated user, asserting they have admin privileges.

    Phase 1: Placeholder — always raises PermissionDenied until Phase 2
    wires up the DB check.

    TODO(phase-2): Check user.is_admin and raise AdminRequiredError if False.
    """
    # TODO(phase-2): Replace with real DB-backed admin check
    raise AdminRequiredError("Admin access is not yet implemented.")
    return user_id  # noqa: unreachable
