"""Gemini provider adapter — Phase 1 stub."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from app.core.constants import COST_TABLE, PROVIDER_GEMINI, QUALITY_SCORES
from app.core.exceptions import ProviderError, VeloraError
from app.providers.base import BaseProvider, ModelConfig


class GeminiProvider(BaseProvider):
    """Adapter for the Google Gemini API."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def get_id(self) -> str:
        return PROVIDER_GEMINI

    def get_available_models(self) -> list[ModelConfig]:
        models_config = COST_TABLE[PROVIDER_GEMINI]
        return [
            ModelConfig(
                model_id=model_id,
                provider_id=PROVIDER_GEMINI,
                context_window=1_048_576,
                cost_input_per_1k=costs["input"],
                cost_output_per_1k=costs["output"],
                quality_score=QUALITY_SCORES.get(model_id, 0.75),
            )
            for model_id, costs in models_config.items()
        ]

    def normalize_request(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        # TODO(phase-2): Convert to Gemini generateContent format
        return {
            "model": model,
            "contents": messages,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            },
        }

    async def call(self, normalized_request: dict) -> AsyncGenerator[str, None]:
        raise NotImplementedError("Gemini provider call is implemented in Phase 2.")
        yield

    def count_tokens(self, messages: list[dict[str, str]], model: str) -> int:
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return total_chars // 4

    def handle_error(self, exception: Exception) -> VeloraError:
        return ProviderError(provider=PROVIDER_GEMINI, message=str(exception))

    async def health_check(self) -> bool:
        return bool(self._api_key)
