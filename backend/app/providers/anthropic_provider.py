"""Anthropic provider adapter — Phase 2 implementation."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

import httpx

from app.core.constants import COST_TABLE, PROVIDER_ANTHROPIC, QUALITY_SCORES
from app.core.exceptions import (
    AuthenticationError,
    ProviderError,
    ServiceUnavailableError,
    VeloraError,
)
from app.providers.base import BaseProvider, ModelConfig

_BASE_URL = "https://api.anthropic.com/v1"
_API_VERSION = "2023-06-01"
_TIMEOUT = httpx.Timeout(120.0, connect=10.0)


class AnthropicProvider(BaseProvider):
    """Adapter for the Anthropic Messages API."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._http = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": _API_VERSION,
                "Content-Type": "application/json",
            },
            timeout=_TIMEOUT,
        )

    def get_id(self) -> str:
        return PROVIDER_ANTHROPIC

    def get_available_models(self) -> list[ModelConfig]:
        return [
            ModelConfig(
                model_id=model_id,
                provider_id=PROVIDER_ANTHROPIC,
                context_window=200_000,
                cost_input_per_1k=costs["input"],
                cost_output_per_1k=costs["output"],
                quality_score=QUALITY_SCORES.get(model_id, 0.75),
            )
            for model_id, costs in COST_TABLE[PROVIDER_ANTHROPIC].items()
        ]

    def normalize_request(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        # Anthropic requires system messages in a top-level "system" field
        system: str | None = None
        filtered: list[dict[str, str]] = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg.get("content", "")
            else:
                filtered.append({"role": msg["role"], "content": msg["content"]})

        req: dict = {
            "model": model,
            "messages": filtered,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        if system:
            req["system"] = system
        return req

    async def call(self, normalized_request: dict) -> AsyncGenerator[str, None]:
        stream_mode = normalized_request.get("stream", True)
        try:
            if stream_mode:
                async with self._http.stream(
                    "POST", "/messages", json=normalized_request
                ) as response:
                    if response.status_code == 401:
                        raise AuthenticationError("Anthropic API key is invalid.")
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        try:
                            event = json.loads(line[6:])
                            if event.get("type") == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        yield text
                        except (json.JSONDecodeError, KeyError):
                            continue
            else:
                req = {**normalized_request, "stream": False}
                response = await self._http.post("/messages", json=req)
                if response.status_code == 401:
                    raise AuthenticationError("Anthropic API key is invalid.")
                response.raise_for_status()
                data = response.json()
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        if text:
                            yield text

        except (AuthenticationError, ProviderError, ServiceUnavailableError):
            raise
        except httpx.HTTPStatusError as exc:
            raise self.handle_error(exc) from exc
        except httpx.TimeoutException as exc:
            raise ServiceUnavailableError("Anthropic request timed out.") from exc

    def count_tokens(self, messages: list[dict[str, str]], model: str) -> int:
        return sum(len(m.get("content", "")) for m in messages) // 4

    def handle_error(self, exception: Exception) -> VeloraError:
        if isinstance(exception, httpx.HTTPStatusError):
            status = exception.response.status_code
            if status == 401:
                return AuthenticationError("Anthropic API key is invalid.")
            if status == 429:
                return ProviderError(provider=PROVIDER_ANTHROPIC, message="Anthropic rate limit exceeded.")
            if status >= 500:
                return ServiceUnavailableError("Anthropic service is temporarily unavailable.")
        return ProviderError(provider=PROVIDER_ANTHROPIC, message=str(exception))

    async def health_check(self) -> bool:
        # Anthropic has no cheap listing endpoint — key presence is the signal
        return bool(self._api_key)
