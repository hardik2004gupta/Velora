"""Cost calculator service — centralised pricing logic.

All pricing lives in ``core/constants.COST_TABLE``.
Never import prices from anywhere else.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.constants import COST_TABLE
from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass(frozen=True)
class CostBreakdown:
    prompt_cost: float       # USD
    completion_cost: float   # USD
    total_cost: float        # USD


class CostService:
    """Calculates estimated USD cost from token counts and the centralized cost table."""

    def calculate(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> CostBreakdown:
        """
        Return a cost breakdown for a completed request.

        Falls back to the provider's average price if the exact model is not in
        the cost table, and returns zero-cost if the provider is unknown.
        """
        provider_costs = COST_TABLE.get(provider, {})
        model_costs = provider_costs.get(model)

        if model_costs is None:
            all_costs = list(provider_costs.values())
            if all_costs:
                input_rate = sum(c["input"] for c in all_costs) / len(all_costs)
                output_rate = sum(c["output"] for c in all_costs) / len(all_costs)
            else:
                input_rate = output_rate = 0.0
            log.warning("cost_table_miss", provider=provider, model=model)
        else:
            input_rate = model_costs["input"]
            output_rate = model_costs["output"]

        prompt_cost = (prompt_tokens / 1_000) * input_rate
        completion_cost = (completion_tokens / 1_000) * output_rate

        return CostBreakdown(
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=prompt_cost + completion_cost,
        )
