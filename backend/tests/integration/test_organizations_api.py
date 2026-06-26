"""Integration tests for organization endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, email: str, password: str = "password123") -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return resp.json()


@pytest.mark.anyio
class TestCreateOrg:
    async def test_create_org_success(self, client: AsyncClient) -> None:
        tokens = await _register_and_login(client, "org_owner@example.com")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        resp = await client.post(
            "/api/v1/organizations",
            json={"name": "Acme Corp"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Acme Corp"
        assert "slug" in data
        assert "id" in data

    async def test_create_org_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/organizations", json={"name": "Ghost Org"})
        assert resp.status_code == 401

    async def test_create_org_slug_collision(self, client: AsyncClient) -> None:
        tokens = await _register_and_login(client, "slug_user@example.com")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        await client.post("/api/v1/organizations", json={"name": "Same Name"}, headers=headers)
        resp = await client.post("/api/v1/organizations", json={"name": "Same Name"}, headers=headers)
        assert resp.status_code == 201
        # slug should be unique (has suffix appended)
        assert resp.json()["slug"] != "same-name"


@pytest.mark.anyio
class TestListOrgs:
    async def test_list_orgs_returns_own_orgs(self, client: AsyncClient) -> None:
        tokens = await _register_and_login(client, "list_orgs_user@example.com")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        await client.post("/api/v1/organizations", json={"name": "My Org"}, headers=headers)

        resp = await client.get("/api/v1/organizations", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        roles = [item["role"] for item in data["items"]]
        assert "owner" in roles


@pytest.mark.anyio
class TestOrgRoleEnforcement:
    async def test_non_owner_cannot_delete_org(self, client: AsyncClient) -> None:
        owner_tokens = await _register_and_login(client, "del_owner@example.com")
        viewer_tokens = await _register_and_login(client, "del_viewer@example.com")

        owner_headers = {"Authorization": f"Bearer {owner_tokens['access_token']}"}
        viewer_headers = {"Authorization": f"Bearer {viewer_tokens['access_token']}"}

        org_resp = await client.post(
            "/api/v1/organizations", json={"name": "Del Test Org"}, headers=owner_headers
        )
        org_id = org_resp.json()["id"]

        # Invite viewer
        await client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "del_viewer@example.com", "role": "viewer"},
            headers=owner_headers,
        )

        # Viewer tries to delete — should be 403
        resp = await client.delete(
            f"/api/v1/organizations/{org_id}",
            headers=viewer_headers,
        )
        assert resp.status_code == 403
