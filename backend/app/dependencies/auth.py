"""
Authentication dependencies.

Injected into protected route handlers via FastAPI's ``Depends()``.

Usage::

    from app.dependencies.auth import get_current_user, require_role

    @router.get("/protected")
    async def protected_route(user = Depends(get_current_user)):
        ...

    @router.delete("/org/{id}")
    async def delete_org(user = Depends(require_role(Role.OWNER))):
        ...
"""

from __future__ import annotations

import uuid
from typing import Callable

from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AdminRequiredError, AuthenticationError, ForbiddenError
from app.core.rbac import Role, role_satisfies
from app.core.security import extract_subject
from app.database.session import get_db_session
from app.models.api_key import APIKey
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.repositories.membership_repository import MembershipRepository
from app.repositories.user_repository import UserRepository

_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Token extraction
# ---------------------------------------------------------------------------


async def get_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> str:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Authorization header is missing or invalid.")
    return credentials.credentials


# ---------------------------------------------------------------------------
# Current user — JWT path
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Optional current user (for routes that work both authenticated and anonymous)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Admin gate
# ---------------------------------------------------------------------------


async def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    """Assert the authenticated user has admin privileges."""
    if not user.is_admin:
        raise AdminRequiredError("Admin access is required.")
    return user


# ---------------------------------------------------------------------------
# API key path
# ---------------------------------------------------------------------------


async def get_current_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> APIKey:
    """
    Verify the ``X-API-Key`` header and return the validated APIKey row.

    Raises:
        AuthenticationError: If the key is missing, invalid, or revoked.
    """
    from app.services.api_key_service import APIKeyService

    raw_key: str | None = request.headers.get("X-API-Key")
    if not raw_key:
        raise AuthenticationError("X-API-Key header is required.")

    service = APIKeyService(db)
    api_key = await service.verify(raw_key)
    if api_key is None:
        raise AuthenticationError("API key is invalid or has been revoked.")
    return api_key


# ---------------------------------------------------------------------------
# Organization context — resolves membership from path param
# ---------------------------------------------------------------------------


async def get_current_org(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> tuple[Organization, Membership]:
    """
    Resolve the ``{org_id}`` path parameter and verify that the current user
    is a member.

    Returns a (Organization, Membership) tuple so routes can inspect the role.

    Raises:
        AuthenticationError: If ``org_id`` is missing from path.
        ForbiddenError / NotFoundError: If the user is not a member.
    """
    from app.core.exceptions import NotFoundError
    from app.repositories.organization_repository import OrganizationRepository

    raw_id = request.path_params.get("org_id")
    if not raw_id:
        raise AuthenticationError("org_id path parameter is required.")
    try:
        org_id = uuid.UUID(raw_id)
    except ValueError:
        raise AuthenticationError("org_id is not a valid UUID.")

    org_repo = OrganizationRepository(db)
    membership_repo = MembershipRepository(db)

    org = await org_repo.get(org_id)
    if org is None:
        raise NotFoundError("Organization not found.")

    membership = await membership_repo.get_by_user_and_org(user.id, org_id)
    if membership is None:
        raise NotFoundError("Organization not found.")

    return org, membership


# ---------------------------------------------------------------------------
# Role-based authorization factories
# ---------------------------------------------------------------------------


def require_role(minimum_role: Role) -> Callable:
    """
    Return a FastAPI dependency that asserts the caller's org role
    meets or exceeds *minimum_role*.

    Usage::

        @router.delete("/orgs/{org_id}")
        async def delete_org(
            org_and_membership = Depends(require_role(Role.OWNER)),
        ):
            org, membership = org_and_membership
            ...
    """

    async def _check_role(
        org_and_membership: tuple[Organization, Membership] = Depends(get_current_org),
    ) -> tuple[Organization, Membership]:
        org, membership = org_and_membership
        if not role_satisfies(membership.role, minimum_role):
            raise ForbiddenError(
                f"Role '{membership.role}' does not meet the minimum required role '{minimum_role}'."
            )
        return org, membership

    return _check_role


def require_owner() -> Callable:
    return require_role(Role.OWNER)


def require_admin() -> Callable:
    return require_role(Role.ADMIN)
