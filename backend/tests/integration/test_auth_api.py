"""Integration tests for authentication endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestRegister:
    async def test_register_success(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "alice@example.com", "password": "securepw1", "full_name": "Alice"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == "alice@example.com"
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    async def test_register_duplicate_email(self, client: AsyncClient) -> None:
        payload = {"email": "dup@example.com", "password": "securepw1", "full_name": "Dup"}
        await client.post("/api/v1/auth/register", json=payload)
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    async def test_register_short_password(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "bob@example.com", "password": "short", "full_name": "Bob"},
        )
        assert resp.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "password123", "full_name": "Bob"},
        )
        assert resp.status_code == 422


@pytest.mark.anyio
class TestLogin:
    @pytest.fixture(autouse=True)
    async def _seed_user(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "login_user@example.com", "password": "password123", "full_name": "Login User"},
        )

    async def test_login_success(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "login_user@example.com", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "login_user@example.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_login_unknown_email(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "password123"},
        )
        assert resp.status_code == 401


@pytest.mark.anyio
class TestRefreshAndLogout:
    @pytest.fixture
    async def tokens(self, client: AsyncClient) -> dict:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "refresh_user@example.com", "password": "password123", "full_name": "Refresh"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "refresh_user@example.com", "password": "password123"},
        )
        return resp.json()

    async def test_refresh_success(self, client: AsyncClient, tokens: dict) -> None:
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        new_tokens = resp.json()
        assert "access_token" in new_tokens
        # New refresh token should differ from old one (rotation)
        assert new_tokens["refresh_token"] != tokens["refresh_token"]

    async def test_refresh_token_rotation_invalidates_old_token(
        self, client: AsyncClient, tokens: dict
    ) -> None:
        # Use the refresh token once
        resp1 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp1.status_code == 200
        # Replay the old token — should be rejected
        resp2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp2.status_code == 401

    async def test_logout_success(self, client: AsyncClient, tokens: dict) -> None:
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        resp = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers=headers,
        )
        assert resp.status_code == 200

    async def test_refresh_after_logout_fails(self, client: AsyncClient, tokens: dict) -> None:
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers=headers,
        )
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp.status_code == 401


@pytest.mark.anyio
class TestMe:
    async def test_me_authenticated(self, client: AsyncClient) -> None:
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": "me_user@example.com", "password": "password123", "full_name": "Me User"},
        )
        access_token = reg.json()["tokens"]["access_token"]
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "me_user@example.com"

    async def test_me_unauthenticated(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.valid.token"},
        )
        assert resp.status_code == 401
