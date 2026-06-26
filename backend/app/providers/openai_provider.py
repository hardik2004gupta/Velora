"""
OpenAI provider adapter.

Implements ``BaseProvider`` for the OpenAI API (gpt-4o, gpt-4o-mini).
Business logic (actual API calls) is implemented in Phase 2.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from app.core.constants import COST_TABLE, PROVIDER_OPENAI, QUALITY_SCORES
from app.core.exceptions import ProviderError, VeloraError
from app.providers.base import BaseProvider, ModelConfig


class OpenAIProvider(BaseProvider):
    """Adapter for the OpenAI Chat Completions API."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def get_id(self) -> str:
        return PROVIDER_OPENAI

    def get_available_models(self) -> list[ModelConfig]:
        models_config = COST_TABLE[PROVIDER_OPENAI]
        return [
            ModelConfig(
                model_id=model_id,
                provider_id=PROVIDER_OPENAI,
                context_window=128_000,
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
        # TODO(phase-2): Implement full OpenAI request normalisation
        return {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

    async def call(self, normalized_request: dict) -> AsyncGenerator[str, None]:
        # TODO(phase-2): Implement httpx streaming call to OpenAI API
        raise NotImplementedError("OpenAI provider call is implemented in Phase 2.")
        yield  # satisfy generator protocol

    def count_tokens(self, messages: list[dict[str, str]], model: str) -> int:
        # TODO(phase-2): Use tiktoken for accurate OpenAI token counting
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return total_chars // 4  # rough approximation: 4 chars ≈ 1 token

    def handle_error(self, exception: Exception) -> VeloraError:
        # TODO(phase-2): Map httpx / OpenAI-specific errors
        return ProviderError(provider=PROVIDER_OPENAI, message=str(exception))

    async def health_check(self) -> bool:
        # TODO(phase-2): Implement a lightweight models-list check
        return bool(self._api_key)
