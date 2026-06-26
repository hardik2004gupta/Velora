"""Unit tests for the LLM provider adapters."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.constants import PROVIDER_ANTHROPIC, PROVIDER_GEMINI, PROVIDER_OPENAI
from app.core.exceptions import AuthenticationError, ProviderError
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import ModelConfig
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def openai() -> OpenAIProvider:
    return OpenAIProvider(api_key="sk-test-openai")


@pytest.fixture
def anthropic() -> AnthropicProvider:
    return AnthropicProvider(api_key="sk-ant-test")


@pytest.fixture
def gemini() -> GeminiProvider:
    return GeminiProvider(api_key="AIza-test")


MESSAGES = [{"role": "user", "content": "Hello, world!"}]


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------


def test_openai_id(openai: OpenAIProvider) -> None:
    assert openai.get_id() == PROVIDER_OPENAI


def test_anthropic_id(anthropic: AnthropicProvider) -> None:
    assert anthropic.get_id() == PROVIDER_ANTHROPIC


def test_gemini_id(gemini: GeminiProvider) -> None:
    assert gemini.get_id() == PROVIDER_GEMINI


# ---------------------------------------------------------------------------
# Available models
# ---------------------------------------------------------------------------


def test_openai_models(openai: OpenAIProvider) -> None:
    models = openai.get_available_models()
    assert len(models) >= 1
    assert all(isinstance(m, ModelConfig) for m in models)
    assert all(m.provider_id == PROVIDER_OPENAI for m in models)


def test_anthropic_models(anthropic: AnthropicProvider) -> None:
    models = anthropic.get_available_models()
    assert len(models) >= 1
    assert all(m.provider_id == PROVIDER_ANTHROPIC for m in models)


def test_gemini_models(gemini: GeminiProvider) -> None:
    models = gemini.get_available_models()
    assert len(models) >= 1
    assert all(m.provider_id == PROVIDER_GEMINI for m in models)


# ---------------------------------------------------------------------------
# normalize_request
# ---------------------------------------------------------------------------


def test_openai_normalize(openai: OpenAIProvider) -> None:
    req = openai.normalize_request(MESSAGES, "gpt-4o-mini", 512, 0.5)
    assert req["model"] == "gpt-4o-mini"
    assert req["messages"] == MESSAGES
    assert req["max_tokens"] == 512
    assert req["temperature"] == 0.5


def test_anthropic_normalize_extracts_system(anthropic: AnthropicProvider) -> None:
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hi"},
    ]
    req = anthropic.normalize_request(messages, "claude-haiku-4-5-20251001", 256, 0.7)
    assert req["system"] == "You are a helpful assistant."
    assert all(m["role"] != "system" for m in req["messages"])


def test_anthropic_normalize_no_system(anthropic: AnthropicProvider) -> None:
    req = anthropic.normalize_request(MESSAGES, "claude-haiku-4-5-20251001", 256, 0.7)
    assert "system" not in req


def test_gemini_normalize_maps_assistant_to_model(gemini: GeminiProvider) -> None:
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    req = gemini.normalize_request(messages, "gemini-2.0-flash", 512, 0.7)
    roles = [c["role"] for c in req["contents"]]
    assert "model" in roles
    assert "assistant" not in roles


# ---------------------------------------------------------------------------
# count_tokens
# ---------------------------------------------------------------------------


def test_token_count_approximation(openai: OpenAIProvider) -> None:
    msgs = [{"role": "user", "content": "a" * 400}]
    tokens = openai.count_tokens(msgs, "gpt-4o-mini")
    assert tokens == 100  # 400 chars / 4


# ---------------------------------------------------------------------------
# handle_error
# ---------------------------------------------------------------------------


def test_openai_handle_401(openai: OpenAIProvider) -> None:
    response = MagicMock()
    response.status_code = 401
    exc = httpx.HTTPStatusError("401", request=MagicMock(), response=response)
    err = openai.handle_error(exc)
    assert isinstance(err, AuthenticationError)


def test_openai_handle_429(openai: OpenAIProvider) -> None:
    response = MagicMock()
    response.status_code = 429
    exc = httpx.HTTPStatusError("429", request=MagicMock(), response=response)
    err = openai.handle_error(exc)
    assert isinstance(err, ProviderError)


def test_anthropic_handle_401(anthropic: AnthropicProvider) -> None:
    response = MagicMock()
    response.status_code = 401
    exc = httpx.HTTPStatusError("401", request=MagicMock(), response=response)
    err = anthropic.handle_error(exc)
    assert isinstance(err, AuthenticationError)


def test_gemini_handle_403(gemini: GeminiProvider) -> None:
    response = MagicMock()
    response.status_code = 403
    exc = httpx.HTTPStatusError("403", request=MagicMock(), response=response)
    err = gemini.handle_error(exc)
    assert isinstance(err, AuthenticationError)


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_openai_health_check_success(openai: OpenAIProvider) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch.object(openai._http, "get", new_callable=AsyncMock, return_value=mock_resp):
        assert await openai.health_check() is True


@pytest.mark.asyncio
async def test_openai_health_check_failure(openai: OpenAIProvider) -> None:
    with patch.object(openai._http, "get", new_callable=AsyncMock, side_effect=httpx.ConnectError("fail")):
        assert await openai.health_check() is False


@pytest.mark.asyncio
async def test_anthropic_health_check(anthropic: AnthropicProvider) -> None:
    assert await anthropic.health_check() is True


@pytest.mark.asyncio
async def test_gemini_health_check_success(gemini: GeminiProvider) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch.object(gemini._http, "get", new_callable=AsyncMock, return_value=mock_resp):
        assert await gemini.health_check() is True
