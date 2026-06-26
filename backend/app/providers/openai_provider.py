"""OpenAI provider adapter — Phase 2 implementation."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

import httpx

from app.core.constants import COST_TABLE, PROVIDER_OPENAI, QUALITY_SCORES
from app.core.exceptions import (
    AuthenticationError,
    ProviderError,
    ServiceUnavailableError,
    VeloraError,
)
from app.providers.base import BaseProvider, ModelConfig

_BASE_URL = "https://api.openai.com/v1"
_TIMEOUT = httpx.Timeout(120.0, connect=10.0)


class OpenAIProvider(BaseProvider):
    """Adapter for the OpenAI Chat Completions API."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._http = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=_TIMEOUT,
        )

    def get_id(self) -> str:
        return PROVIDER_OPENAI

    def get_available_models(self) -> list[ModelConfig]:
        return [
            ModelConfig(
                model_id=model_id,
                provider_id=PROVIDER_OPENAI,
                context_window=128_000,
                cost_input_per_1k=costs["input"],
                cost_output_per_1k=costs["output"],
                quality_score=QUALITY_SCORES.get(model_id, 0.75),
            )
            for model_id, costs in COST_TABLE[PROVIDER_OPENAI].items()
        ]

    def normalize_request(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        return {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

    async def call(self, normalized_request: dict) -> AsyncGenerator[str, None]:
        stream_mode = normalized_request.get("stream", True)
        try:
            if stream_mode:
                async with self._http.stream(
                    "POST", "/chat/completions", json=normalized_request
                ) as response:
                    if response.status_code == 401:
                        raise AuthenticationError("OpenAI API key is invalid or expired.")
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:].strip()
                        if data == "[DONE]":
                            return
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {}).get("content") or ""
                            if delta:
                                yield delta
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
            else:
                req = {**normalized_request, "stream": False}
                response = await self._http.post("/chat/completions", json=req)
                if response.status_code == 401:
                    raise AuthenticationError("OpenAI API key is invalid or expired.")
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"].get("content") or ""
                if content:
                    yield content

        except (AuthenticationError, ProviderError, ServiceUnavailableError):
            raise
        except httpx.HTTPStatusError as exc:
            raise self.handle_error(exc) from exc
        except httpx.TimeoutException as exc:
            raise ServiceUnavailableError("OpenAI request timed out.") from exc

    def count_tokens(self, messages: list[dict[str, str]], model: str) -> int:
        # Approximation: 4 chars ≈ 1 token (tiktoken not yet imported)
        return sum(len(m.get("content", "")) for m in messages) // 4

    def handle_error(self, exception: Exception) -> VeloraError:
        if isinstance(exception, httpx.HTTPStatusError):
            status = exception.response.status_code
            if status == 401:
                return AuthenticationError("OpenAI API key is invalid or expired.")
            if status == 429:
                return ProviderError(provider=PROVIDER_OPENAI, message="OpenAI rate limit exceeded.")
            if status >= 500:
                return ServiceUnavailableError("OpenAI service is temporarily unavailable.")
        return ProviderError(provider=PROVIDER_OPENAI, message=str(exception))

    async def health_check(self) -> bool:
        try:
            response = await self._http.get("/models", timeout=httpx.Timeout(5.0))
            return response.status_code == 200
        except Exception:
            return False
