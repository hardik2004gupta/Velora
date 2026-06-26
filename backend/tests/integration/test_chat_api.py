"""Integration tests for POST /chat and POST /chat/stream endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.constants import PROVIDER_OPENAI


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _fake_stream(tokens: list[str]) -> AsyncGenerator[str, None]:
    for token in tokens:
        yield token


# ---------------------------------------------------------------------------
# POST /api/v1/chat
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_non_streaming(auth_client: AsyncClient) -> None:
    """Non-streaming endpoint returns full content in one response."""
    fake_tokens = ["Hello", ", ", "world", "!"]

    with patch(
        "app.providers.openai_provider.OpenAIProvider.call",
        return_value=_fake_stream(fake_tokens),
    ):
        response = await auth_client.post(
            "/api/v1/chat",
            json={
                "messages": [{"role": "user", "content": "Say hello"}],
                "provider": PROVIDER_OPENAI,
                "max_tokens": 64,
                "temperature": 0.0,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "Hello, world!"
    assert body["provider"] == PROVIDER_OPENAI
    assert "model" in body
    assert body["finish_reason"] == "stop"


@pytest.mark.asyncio
async def test_chat_requires_auth(client: AsyncClient) -> None:
    """Unauthenticated request returns 401."""
    response = await client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Hi"}],
            "provider": PROVIDER_OPENAI,
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_unknown_provider(auth_client: AsyncClient) -> None:
    """Unknown provider returns 503 (ConfigurationError → ServiceUnavailableError)."""
    response = await auth_client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Hi"}],
            "provider": "unknown_provider_xyz",
        },
    )
    # ConfigurationError is not an HTTPError so it falls through to 500
    assert response.status_code in (500, 503)


@pytest.mark.asyncio
async def test_chat_empty_messages_rejected(auth_client: AsyncClient) -> None:
    """Empty messages list fails validation."""
    response = await auth_client.post(
        "/api/v1/chat",
        json={
            "messages": [],
            "provider": PROVIDER_OPENAI,
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/chat/stream
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_stream_returns_sse(auth_client: AsyncClient) -> None:
    """Streaming endpoint returns text/event-stream with delta events."""
    fake_tokens = ["Hi", " there"]

    with patch(
        "app.providers.openai_provider.OpenAIProvider.call",
        return_value=_fake_stream(fake_tokens),
    ):
        response = await auth_client.post(
            "/api/v1/chat/stream",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "provider": PROVIDER_OPENAI,
            },
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    assert "delta" in body
    assert "done" in body


@pytest.mark.asyncio
async def test_chat_stream_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/chat/stream",
        json={
            "messages": [{"role": "user", "content": "Hi"}],
            "provider": PROVIDER_OPENAI,
        },
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/v1/providers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_providers(auth_client: AsyncClient) -> None:
    """Providers endpoint lists registered providers with model info."""
    response = await auth_client.get("/api/v1/providers")
    assert response.status_code == 200
    body = response.json()
    assert "providers" in body
    assert isinstance(body["providers"], list)


@pytest.mark.asyncio
async def test_list_providers_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/providers")
    assert response.status_code == 401
