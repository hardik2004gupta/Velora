"""Unit tests for CostService — pure arithmetic, no DB."""

from __future__ import annotations

import pytest

from app.services.cost_service import CostBreakdown, CostService


@pytest.fixture()
def svc() -> CostService:
    return CostService()


class TestKnownModels:
    def test_gpt4o_mini(self, svc: CostService) -> None:
        result = svc.calculate("openai", "gpt-4o-mini", 1000, 500)
        assert result.prompt_cost == pytest.approx(0.00015)      # 1000/1k * 0.00015
        assert result.completion_cost == pytest.approx(0.0003)   # 500/1k  * 0.0006
        assert result.total_cost == pytest.approx(0.00045)

    def test_gpt4o(self, svc: CostService) -> None:
        result = svc.calculate("openai", "gpt-4o", 2000, 1000)
        assert result.prompt_cost == pytest.approx(0.005)        # 2000/1k * 0.0025
        assert result.completion_cost == pytest.approx(0.01)     # 1000/1k * 0.01
        assert result.total_cost == pytest.approx(0.015)

    def test_claude_haiku(self, svc: CostService) -> None:
        result = svc.calculate("anthropic", "claude-haiku-4-5-20251001", 500, 200)
        assert result.prompt_cost == pytest.approx(0.0004)       # 500/1k  * 0.0008
        assert result.completion_cost == pytest.approx(0.0008)   # 200/1k  * 0.004
        assert result.total_cost == pytest.approx(0.0012)

    def test_gemini_flash(self, svc: CostService) -> None:
        result = svc.calculate("gemini", "gemini-2.0-flash", 10_000, 5_000)
        assert result.prompt_cost == pytest.approx(1.0)          # 10000/1k * 0.0001
        assert result.completion_cost == pytest.approx(2.0)      # 5000/1k  * 0.0004
        assert result.total_cost == pytest.approx(3.0)


class TestZeroTokens:
    def test_zero_tokens(self, svc: CostService) -> None:
        result = svc.calculate("openai", "gpt-4o-mini", 0, 0)
        assert result.prompt_cost == 0.0
        assert result.completion_cost == 0.0
        assert result.total_cost == 0.0


class TestUnknownModel:
    def test_unknown_model_falls_back_to_provider_average(self, svc: CostService) -> None:
        result = svc.calculate("openai", "nonexistent-model", 1000, 1000)
        assert result.total_cost >= 0.0
        assert isinstance(result, CostBreakdown)

    def test_unknown_provider_returns_zero(self, svc: CostService) -> None:
        result = svc.calculate("unknown_provider", "some-model", 1000, 500)
        assert result.total_cost == 0.0


class TestReturnType:
    def test_returns_cost_breakdown(self, svc: CostService) -> None:
        result = svc.calculate("gemini", "gemini-2.0-pro", 100, 100)
        assert isinstance(result, CostBreakdown)
        assert result.total_cost == pytest.approx(result.prompt_cost + result.completion_cost)

    def test_frozen_dataclass(self, svc: CostService) -> None:
        result = svc.calculate("openai", "gpt-4o-mini", 100, 100)
        with pytest.raises(Exception):
            result.total_cost = 99.0  # type: ignore[misc]
