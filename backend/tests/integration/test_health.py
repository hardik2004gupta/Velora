"""Integration tests for health endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthEndpoints:
    async def test_liveness_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health/live")
        assert response.status_code == 200
        assert response.json()["alive"] is True

    async def test_version_returns_app_info(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/version")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Velora"
        assert "version" in data
        assert "environment" in data

    async def test_health_endpoint_structure(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health")
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data
        assert "dependencies" in data
        assert "database" in data["dependencies"]
        assert "redis" in data["dependencies"]

    async def test_request_id_header_present(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health/live")
        assert "x-request-id" in response.headers

    async def test_process_time_header_present(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health/live")
        assert "x-process-time-ms" in response.headers
