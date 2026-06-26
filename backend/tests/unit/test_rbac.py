"""Unit tests for RBAC role/permission logic."""

from __future__ import annotations

import pytest

from app.core.rbac import Permission, Role, has_permission, role_satisfies


class TestRoleSatisfies:
    def test_owner_satisfies_all(self) -> None:
        for role in Role:
            assert role_satisfies(Role.OWNER, role)

    def test_viewer_satisfies_only_viewer(self) -> None:
        assert role_satisfies(Role.VIEWER, Role.VIEWER)
        assert not role_satisfies(Role.VIEWER, Role.DEVELOPER)
        assert not role_satisfies(Role.VIEWER, Role.ADMIN)
        assert not role_satisfies(Role.VIEWER, Role.OWNER)

    def test_admin_satisfies_developer_and_below(self) -> None:
        assert role_satisfies(Role.ADMIN, Role.DEVELOPER)
        assert role_satisfies(Role.ADMIN, Role.VIEWER)
        assert role_satisfies(Role.ADMIN, Role.ADMIN)
        assert not role_satisfies(Role.ADMIN, Role.OWNER)

    def test_developer_satisfies_viewer_and_self(self) -> None:
        assert role_satisfies(Role.DEVELOPER, Role.VIEWER)
        assert role_satisfies(Role.DEVELOPER, Role.DEVELOPER)
        assert not role_satisfies(Role.DEVELOPER, Role.ADMIN)

    def test_accepts_string_roles(self) -> None:
        assert role_satisfies("owner", "viewer")
        assert not role_satisfies("viewer", "owner")


class TestHasPermission:
    def test_owner_can_delete_org(self) -> None:
        assert has_permission(Role.OWNER, Permission.DELETE_ORGANIZATION)

    def test_admin_cannot_delete_org(self) -> None:
        assert not has_permission(Role.ADMIN, Permission.DELETE_ORGANIZATION)

    def test_admin_can_manage_api_keys(self) -> None:
        assert has_permission(Role.ADMIN, Permission.MANAGE_API_KEYS)

    def test_developer_can_manage_api_keys(self) -> None:
        # MANAGE_API_KEYS requires DEVELOPER rank minimum
        assert has_permission(Role.DEVELOPER, Permission.MANAGE_API_KEYS)

    def test_viewer_cannot_manage_api_keys(self) -> None:
        assert not has_permission(Role.VIEWER, Permission.MANAGE_API_KEYS)

    def test_developer_can_view_api_keys(self) -> None:
        assert has_permission(Role.DEVELOPER, Permission.VIEW_API_KEYS)

    def test_viewer_can_view_analytics(self) -> None:
        assert has_permission(Role.VIEWER, Permission.VIEW_ANALYTICS)

    def test_viewer_cannot_use_gateway(self) -> None:
        assert not has_permission(Role.VIEWER, Permission.USE_GATEWAY)

    def test_developer_can_use_gateway(self) -> None:
        assert has_permission(Role.DEVELOPER, Permission.USE_GATEWAY)

    def test_all_roles_can_view_organization(self) -> None:
        for role in Role:
            assert has_permission(role, Permission.VIEW_ORGANIZATION)
