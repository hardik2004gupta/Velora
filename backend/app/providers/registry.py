"""
Provider registry — maps provider IDs to instantiated adapters.

The registry is populated during application startup (lifespan handler)
based on which API keys are present in settings.  If a provider's key is
absent, that provider is silently skipped.

Usage::

    from app.providers.registry import ProviderRegistry

    registry = ProviderRegistry()
    provider = registry.get("openai")
    models = registry.get_all_models()
"""

from __future__ import annotations

from app.config import get_settings
from app.core.exceptions import ConfigurationError
from app.core.logging import get_logger
from app.providers.base import BaseProvider, ModelConfig

log = get_logger(__name__)


class ProviderRegistry:
    """Manages instantiated LLM provider adapters."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        """Register a provider adapter instance."""
        pid = provider.get_id()
        self._providers[pid] = provider
        log.info("provider_registered", provider=pid)

    def get(self, provider_id: str) -> BaseProvider:
        """
        Return the provider adapter for *provider_id*.

        Raises:
            ConfigurationError: If the provider is not registered.
        """
        provider = self._providers.get(provider_id)
        if provider is None:
            raise ConfigurationError(
                f"Provider '{provider_id}' is not registered. "
                f"Available: {list(self._providers)}"
            )
        return provider

    def get_all(self) -> list[BaseProvider]:
        """Return all registered provider adapters."""
        return list(self._providers.values())

    def get_all_models(self) -> list[ModelConfig]:
        """Return every model offered across all registered providers."""
        models = []
        for provider in self._providers.values():
            models.extend(provider.get_available_models())
        return models

    def is_registered(self, provider_id: str) -> bool:
        """Return True if *provider_id* has been registered."""
        return provider_id in self._providers

    def provider_ids(self) -> list[str]:
        """Return a sorted list of registered provider IDs."""
        return sorted(self._providers)

    def setup_from_settings(self) -> None:
        """
        Register providers based on which API keys are configured.

        Skips any provider whose API key is absent.  Logs a warning so
        operators know which providers are inactive.
        """
        # Import here to avoid circular imports at module level
        from app.providers.anthropic_provider import AnthropicProvider
        from app.providers.gemini_provider import GeminiProvider
        from app.providers.openai_provider import OpenAIProvider

        settings = get_settings()

        candidates: list[tuple[str, str | None, type[BaseProvider]]] = [
            ("openai", settings.openai_api_key, OpenAIProvider),
            ("anthropic", settings.anthropic_api_key, AnthropicProvider),
            ("gemini", settings.gemini_api_key, GeminiProvider),
        ]

        for provider_id, api_key, cls in candidates:
            if api_key:
                self.register(cls(api_key=api_key))
            else:
                log.warning(
                    "provider_skipped",
                    provider=provider_id,
                    reason="API key not configured",
                )

        if not self._providers:
            raise ConfigurationError(
                "No LLM providers are configured. "
                "Set at least one of OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY."
            )


# Module-level singleton
_registry: ProviderRegistry | None = None


def get_registry() -> ProviderRegistry:
    """Return the global provider registry singleton."""
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry
