"""
Role-Based Access Control (RBAC).

Roles (ordered from highest to lowest privilege):
    OWNER      → Full control: manage org, billing, delete org
    ADMIN      → Manage members, API keys, view all requests
    DEVELOPER  → Create/delete own API keys, use the gateway
    VIEWER     → Read-only: view requests, analytics, provider status

Each role implicitly inherits all permissions of roles below it.

Usage::

    from app.core.rbac import Role, Permission, has_permission

    if has_permission(user_role, Permission.MANAGE_MEMBERS):
        ...
"""

from __future__ import annotations

from enum import IntEnum, StrEnum


class Role(StrEnum):
    """Organization membership roles, ordered by privilege level."""

    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


# Numeric rank — higher = more privileged.  Used for hierarchy checks.
_ROLE_RANK: dict[Role, int] = {
    Role.OWNER: 40,
    Role.ADMIN: 30,
    Role.DEVELOPER: 20,
    Role.VIEWER: 10,
}


class Permission(StrEnum):
    """Granular permissions used in authorization checks."""

    # Organization management
    DELETE_ORGANIZATION = "delete_organization"
    UPDATE_ORGANIZATION = "update_organization"
    VIEW_ORGANIZATION = "view_organization"

    # Member management
    MANAGE_MEMBERS = "manage_members"
    VIEW_MEMBERS = "view_members"

    # API key management
    MANAGE_API_KEYS = "manage_api_keys"
    VIEW_API_KEYS = "view_api_keys"

    # Gateway usage
    USE_GATEWAY = "use_gateway"

    # Analytics / history
    VIEW_ANALYTICS = "view_analytics"


# Permission → minimum role required
_PERMISSION_REQUIREMENTS: dict[Permission, Role] = {
    Permission.DELETE_ORGANIZATION: Role.OWNER,
    Permission.UPDATE_ORGANIZATION: Role.ADMIN,
    Permission.VIEW_ORGANIZATION: Role.VIEWER,
    Permission.MANAGE_MEMBERS: Role.ADMIN,
    Permission.VIEW_MEMBERS: Role.VIEWER,
    Permission.MANAGE_API_KEYS: Role.DEVELOPER,
    Permission.VIEW_API_KEYS: Role.VIEWER,
    Permission.USE_GATEWAY: Role.DEVELOPER,
    Permission.VIEW_ANALYTICS: Role.VIEWER,
}


def has_permission(role: str | Role, permission: Permission) -> bool:
    """
    Return True if *role* satisfies the minimum requirement for *permission*.

    Args:
        role: The user's role string (e.g. ``"admin"``).
        permission: The permission being checked.

    Returns:
        True if the role's rank ≥ the required role's rank.
    """
    try:
        actual_role = Role(role)
    except ValueError:
        return False

    required_role = _PERMISSION_REQUIREMENTS.get(permission)
    if required_role is None:
        return False

    return _ROLE_RANK[actual_role] >= _ROLE_RANK[required_role]


def role_satisfies(actual: str | Role, minimum: str | Role) -> bool:
    """
    Return True if *actual* role is at least as privileged as *minimum*.

    Example::

        role_satisfies("admin", "developer")  # True
        role_satisfies("viewer", "admin")     # False
    """
    try:
        a = Role(actual)
        m = Role(minimum)
    except ValueError:
        return False
    return _ROLE_RANK[a] >= _ROLE_RANK[m]
