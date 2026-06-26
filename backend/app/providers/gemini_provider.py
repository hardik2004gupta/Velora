"""Google Gemini provider adapter — Phase 2 implementation."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

import httpx

from app.core.constants import COST_TABLE, PROVIDER_GEMINI, QUALITY_SCORES
from app.core.exceptions import (
    AuthenticationError,
    ProviderError,
    ServiceUnavailableError,
    VeloraError,
)
from app.providers.base import BaseProvider, ModelConfig

_BASE_URL = "https://generativelanguage.googleapis.com"
_TIMEOUT = httpx.Timeout(120.0, connect=10.0)


def _to_gemini_messages(messages: list[dict[str, str]]) -> list[dict]:
    """Convert Velora-standard messages to Gemini `contents` format.

    - "system" role has no native equivalent; prepend as a user turn.
    - "assistant" role maps to "model".
    """
    contents: list[dict] = []
    for msg in messages:
        role = msg["role"]
        content = msg.get("content", "")
        if role == "system":
            contents.append({"role": "user", "parts": [{"text": f"[System]: {content}"}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
        else:
            contents.append({"role": "user", "parts": [{"text": content}]})
    return contents


class GeminiProvider(BaseProvider):
    """Adapter for the Google Gemini generateContent API."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._http = httpx.AsyncClient(base_url=_BASE_URL, timeout=_TIMEOUT)

    def get_id(self) -> str:
        return PROVIDER_GEMINI

    def get_available_models(self) -> list[ModelConfig]:
        return [
            ModelConfig(
                model_id=model_id,
                provider_id=PROVIDER_GEMINI,
                context_window=1_048_576,
                cost_input_per_1k=costs["input"],
                cost_output_per_1k=costs["output"],
                quality_score=QUALITY_SCORES.get(model_id, 0.75),
            )
            for model_id, costs in COST_TABLE[PROVIDER_GEMINI].items()
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
            "contents": _to_gemini_messages(messages),
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
            "stream": True,  # internal control flag
        }

    async def call(self, normalized_request: dict) -> AsyncGenerator[str, None]:
        model = normalized_request["model"]
        stream_mode = normalized_request.get("stream", True)
        body = {
            "contents": normalized_request["contents"],
            "generationConfig": normalized_request["generationConfig"],
        }
        try:
            if stream_mode:
                url = f"/v1beta/models/{model}:streamGenerateContent"
                params = {"key": self._api_key, "alt": "sse"}
                async with self._http.stream("POST", url, json=body, params=params) as response:
                    if response.status_code in (400, 403):
                        raise AuthenticationError("Gemini API key is invalid or request is malformed.")
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        try:
                            event = json.loads(line[6:])
                            for candidate in event.get("candidates", []):
                                for part in candidate.get("content", {}).get("parts", []):
                                    text = part.get("text", "")
                                    if text:
                                        yield text
                        except (json.JSONDecodeError, KeyError):
                            continue
            else:
                url = f"/v1beta/models/{model}:generateContent"
                params = {"key": self._api_key}
                response = await self._http.post(url, json=body, params=params)
                if response.status_code in (400, 403):
                    raise AuthenticationError("Gemini API key is invalid or request is malformed.")
                response.raise_for_status()
                data = response.json()
                for candidate in data.get("candidates", []):
                    for part in candidate.get("content", {}).get("parts", []):
                        text = part.get("text", "")
                        if text:
                            yield text

        except (AuthenticationError, ProviderError, ServiceUnavailableError):
            raise
        except httpx.HTTPStatusError as exc:
            raise self.handle_error(exc) from exc
        except httpx.TimeoutException as exc:
            raise ServiceUnavailableError("Gemini request timed out.") from exc

    def count_tokens(self, messages: list[dict[str, str]], model: str) -> int:
        return sum(len(m.get("content", "")) for m in messages) // 4

    def handle_error(self, exception: Exception) -> VeloraError:
        if isinstance(exception, httpx.HTTPStatusError):
            status = exception.response.status_code
            if status in (400, 403):
                return AuthenticationError("Gemini API key is invalid.")
            if status == 429:
                return ProviderError(provider=PROVIDER_GEMINI, message="Gemini rate limit exceeded.")
            if status >= 500:
                return ServiceUnavailableError("Gemini service is temporarily unavailable.")
        return ProviderError(provider=PROVIDER_GEMINI, message=str(exception))

    async def health_check(self) -> bool:
        try:
            response = await self._http.get(
                "/v1beta/models",
                params={"key": self._api_key},
                timeout=httpx.Timeout(5.0),
            )
            return response.status_code == 200
        except Exception:
            return False
