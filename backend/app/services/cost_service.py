"""
Cost calculation service.

Converts token counts into USD cost using the static COST_TABLE.
This is the only place in the codebase that performs cost arithmetic.

Usage::

    from app.services.cost_service import CostService

    cost = CostService.calculate(
        provider="openai",
        model="gpt-4o-mini",
        prompt_tokens=100,
        completion_tokens=250,
    )
"""

from __future__ import annotations

from app.core.constants import COST_TABLE
from app.core.exceptions import ConfigurationError


class CostService:
    """Stateless service for token-to-USD cost calculation."""

    @staticmethod
    def calculate(
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Calculate the total cost in USD for a completed request.

        Args:
            provider: Provider ID (e.g. ``"openai"``).
            model: Model ID (e.g. ``"gpt-4o-mini"``).
            prompt_tokens: Number of input tokens billed.
            completion_tokens: Number of output tokens billed.

        Returns:
            Total cost in USD, rounded to 8 decimal places.

        Raises:
            ConfigurationError: If the provider/model combination is not in COST_TABLE.
        """
        provider_costs = COST_TABLE.get(provider)
        if provider_costs is None:
            raise ConfigurationError(f"Provider '{provider}' not found in COST_TABLE.")

        model_costs = provider_costs.get(model)
        if model_costs is None:
            raise ConfigurationError(
                f"Model '{model}' not found for provider '{provider}' in COST_TABLE."
            )

        input_cost = (prompt_tokens / 1000) * model_costs["input"]
        output_cost = (completion_tokens / 1000) * model_costs["output"]
        return round(input_cost + output_cost, 8)

    @staticmethod
    def get_cost_per_1k(provider: str, model: str) -> float:
        """
        Return a combined cost-per-1K-tokens figure for routing comparisons.

        Uses a 30/70 input/output split as a heuristic for typical requests.
        """
        provider_costs = COST_TABLE.get(provider, {})
        model_costs = provider_costs.get(model, {})
        input_rate = model_costs.get("input", 0.0)
        output_rate = model_costs.get("output", 0.0)
        return 0.30 * input_rate + 0.70 * output_rate
