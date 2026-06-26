"""
Abstract base class for all LLM provider adapters.

Adding a new provider:
1. Create ``app/providers/{name}_provider.py`` implementing ``BaseProvider``.
2. Add cost entries to ``COST_TABLE`` in ``core/constants.py``.
3. Add quality scores to ``QUALITY_SCORES`` in ``core/constants.py``.
4. Register the provider in ``ProviderRegistry``.

That's it — the router, cache, and analytics layers pick it up automatically.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from app.core.exceptions import VeloraError


@dataclass(frozen=True)
class ModelConfig:
    """Static configuration for a single model offered by a provider."""

    model_id: str
    provider_id: str
    context_window: int
    cost_input_per_1k: float   # USD
    cost_output_per_1k: float  # USD
    quality_score: float       # 0.0 – 1.0
    supports_streaming: bool = True


class BaseProvider(ABC):
    """
    Abstract adapter for an LLM provider.

    All I/O is async.  The streaming path yields raw string deltas so the
    streaming engine can forward them directly to the client via SSE.
    """

    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------

    @abstractmethod
    def get_id(self) -> str:
        """Return the provider identifier (e.g. ``"openai"``)."""

    @abstractmethod
    def get_available_models(self) -> list[ModelConfig]:
        """Return every model this provider supports."""

    # -------------------------------------------------------------------------
    # Request normalisation
    # -------------------------------------------------------------------------

    @abstractmethod
    def normalize_request(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        """
        Convert a Velora-standard request into the provider's native API format.

        Args:
            messages: List of ``{"role": ..., "content": ...}`` dicts.
            model: Provider-specific model ID string.
            max_tokens: Maximum completion tokens.
            temperature: Sampling temperature.

        Returns:
            A dict that can be passed directly to the provider's HTTP API.
        """

    # -------------------------------------------------------------------------
    # Inference
    # -------------------------------------------------------------------------

    @abstractmethod
    async def call(
        self,
        normalized_request: dict,
    ) -> AsyncGenerator[str, None]:
        """
        Execute the inference request and yield raw token strings.

        This is the streaming path.  The caller is responsible for assembling
        the full response if needed.

        Args:
            normalized_request: Output of ``normalize_request()``.

        Yields:
            Raw text deltas from the provider stream.

        Raises:
            ProviderError: On any provider-side failure.
        """
        # Satisfy the generator protocol — implementations must use ``yield``
        yield  # type: ignore[misc]

    # -------------------------------------------------------------------------
    # Token counting
    # -------------------------------------------------------------------------

    @abstractmethod
    def count_tokens(self, messages: list[dict[str, str]], model: str) -> int:
        """
        Estimate the number of prompt tokens for the given messages.

        Used for cost preview before the actual call.  Accuracy depends on the
        provider's tokeniser — this is an estimate, not a guarantee.
        """

    # -------------------------------------------------------------------------
    # Error normalisation
    # -------------------------------------------------------------------------

    @abstractmethod
    def handle_error(self, exception: Exception) -> VeloraError:
        """
        Translate a provider-specific exception into a Velora exception.

        Implementations should map known HTTP status codes and exception types
        to the appropriate ``ProviderError`` or ``ServiceUnavailableError``.
        """

    # -------------------------------------------------------------------------
    # Health
    # -------------------------------------------------------------------------

    async def health_check(self) -> bool:
        """
        Perform a lightweight check to determine if the provider is reachable.

        Default implementation returns True (overridden by concrete providers).
        Phase 2 will wire this into the background health checker.
        """
        return True

    def __repr__(self) -> str:
        return f"<Provider id={self.get_id()!r}>"
