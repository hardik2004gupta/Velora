"""Unit tests for CostService."""

from __future__ import annotations

import pytest

from app.core.exceptions import ConfigurationError
from app.services.cost_service import CostService


class TestCostServiceCalculate:
    """Tests for CostService.calculate()."""

    def test_openai_gpt4o_mini_cost(self) -> None:
        cost = CostService.calculate(
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500,
        )
        # input: 1000/1000 * 0.00015 = 0.00015
        # output: 500/1000 * 0.0006 = 0.0003
        # total: 0.00045
        assert cost == pytest.approx(0.00045, rel=1e-6)

    def test_anthropic_haiku_cost(self) -> None:
        cost = CostService.calculate(
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
            prompt_tokens=2000,
            completion_tokens=1000,
        )
        # input: 2000/1000 * 0.0008 = 0.0016
        # output: 1000/1000 * 0.004 = 0.004
        # total: 0.0056
        assert cost == pytest.approx(0.0056, rel=1e-6)

    def test_zero_tokens_returns_zero(self) -> None:
        cost = CostService.calculate(
            provider="openai",
            model="gpt-4o-mini",
            prompt_tokens=0,
            completion_tokens=0,
        )
        assert cost == 0.0

    def test_unknown_provider_raises(self) -> None:
        with pytest.raises(ConfigurationError, match="not found in COST_TABLE"):
            CostService.calculate(
                provider="unknown_provider",
                model="some-model",
                prompt_tokens=100,
                completion_tokens=100,
            )

    def test_unknown_model_raises(self) -> None:
        with pytest.raises(ConfigurationError, match="not found for provider"):
            CostService.calculate(
                provider="openai",
                model="gpt-99-ultra",
                prompt_tokens=100,
                completion_tokens=100,
            )

    def test_result_rounded_to_8_decimal_places(self) -> None:
        cost = CostService.calculate(
            provider="gemini",
            model="gemini-2.0-flash",
            prompt_tokens=1,
            completion_tokens=1,
        )
        assert len(str(cost).split(".")[-1]) <= 8


class TestCostServiceGetCostPer1K:
    """Tests for CostService.get_cost_per_1k()."""

    def test_returns_float(self) -> None:
        result = CostService.get_cost_per_1k("openai", "gpt-4o-mini")
        assert isinstance(result, float)
        assert result > 0

    def test_unknown_provider_returns_zero(self) -> None:
        result = CostService.get_cost_per_1k("unknown", "unknown-model")
        assert result == 0.0
