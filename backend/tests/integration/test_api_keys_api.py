"""Integration tests for personal API key endpoints (/api-keys)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, email: str) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": "Test User"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    return resp.json()


@pytest.mark.anyio
class TestCreateAPIKey:
    async def test_create_key_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/api-keys", json={"name": "key"})
        assert resp.status_code == 401

    async def test_create_key_success(self, client: AsyncClient) -> None:
        tokens = await _register_and_login(client, "apikey_create@example.com")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        resp = await client.post("/api/v1/api-keys", json={"name": "My Key"}, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert "key" in data
        assert data["key"].startswith("vk-")
        assert data["name"] == "My Key"


@pytest.mark.anyio
class TestListAPIKeys:
    async def test_list_keys_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/api-keys")
        assert resp.status_code == 401

    async def test_list_keys_empty_for_new_user(self, client: AsyncClient) -> None:
        tokens = await _register_and_login(client, "apikey_list@example.com")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        resp = await client.get("/api/v1/api-keys", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []


@pytest.mark.anyio
class TestRevokeAPIKey:
    async def test_revoke_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.delete("/api/v1/api-keys/00000000-0000-0000-0000-000000000001")
        assert resp.status_code == 401
