"""Unit tests for RouterService — all routing strategies."""

from __future__ import annotations

import pytest

from app.core.constants import (
    STRATEGY_AUTO,
    STRATEGY_CHEAPEST,
    STRATEGY_FASTEST,
    STRATEGY_QUALITY,
    STATUS_DOWN,
    STATUS_HEALTHY,
)
from app.core.exceptions import BadRequestError, ServiceUnavailableError
from app.providers.base import BaseProvider, ModelConfig
from app.providers.registry import ProviderRegistry
from app.services.router_service import RouterService


# ---------------------------------------------------------------------------
# Fake providers for testing
# ---------------------------------------------------------------------------


class _FakeProvider(BaseProvider):
    def __init__(self, pid: str, models: list[ModelConfig]) -> None:
        self._id = pid
        self._models = models

    def get_id(self) -> str:
        return self._id

    def get_available_models(self) -> list[ModelConfig]:
        return self._models

    def normalize_request(self, messages, model, max_tokens, temperature):  # type: ignore[override]
        return {}

    async def call(self, normalized):  # type: ignore[override]
        yield ""

    def count_tokens(self, messages, model):  # type: ignore[override]
        return 0

    def handle_error(self, exc):  # type: ignore[override]
        raise exc


def _make_model(
    model_id: str,
    cost_input: float,
    cost_output: float,
    quality: float,
    provider_id: str = "test",
) -> ModelConfig:
    return ModelConfig(
        model_id=model_id,
        provider_id=provider_id,
        context_window=8192,
        cost_input_per_1k=cost_input,
        cost_output_per_1k=cost_output,
        quality_score=quality,
        supports_streaming=True,
    )


def _make_registry(*providers: _FakeProvider) -> ProviderRegistry:
    registry = ProviderRegistry()
    for p in providers:
        registry.register(p)
    return registry


# Three fake providers with distinct cost/latency/quality profiles
_OPENAI = _FakeProvider(
    "openai",
    [
        _make_model("gpt-4o", 0.0025, 0.01, 0.92, "openai"),
        _make_model("gpt-4o-mini", 0.00015, 0.0006, 0.78, "openai"),
    ],
)

_ANTHROPIC = _FakeProvider(
    "anthropic",
    [
        _make_model("claude-sonnet-4-6", 0.003, 0.015, 0.90, "anthropic"),
        _make_model("claude-haiku-4-5-20251001", 0.0008, 0.004, 0.80, "anthropic"),
    ],
)

_GEMINI = _FakeProvider(
    "gemini",
    [
        _make_model("gemini-2.0-flash", 0.0001, 0.0004, 0.75, "gemini"),
        _make_model("gemini-2.0-pro", 0.0035, 0.0105, 0.88, "gemini"),
    ],
)


@pytest.fixture()
def registry() -> ProviderRegistry:
    return _make_registry(_OPENAI, _ANTHROPIC, _GEMINI)


@pytest.fixture()
def svc(registry: ProviderRegistry) -> RouterService:
    return RouterService(registry)


# ---------------------------------------------------------------------------
# Cheapest strategy
# ---------------------------------------------------------------------------


class TestCheapestStrategy:
    def test_selects_cheapest_model(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_CHEAPEST)
        # gemini-2.0-flash avg cost = (0.0001 + 0.0004) / 2 = 0.00025 — cheapest
        assert result.selected_provider_id == "gemini"
        assert result.selected_model == "gemini-2.0-flash"

    def test_strategy_field(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_CHEAPEST)
        assert result.strategy == STRATEGY_CHEAPEST

    def test_candidates_sorted_by_score_desc(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_CHEAPEST)
        scores = [c.score for c in result.candidates]
        assert scores == sorted(scores, reverse=True)

    def test_score_breakdown_has_cost_key(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_CHEAPEST)
        for c in result.candidates:
            assert "cost" in c.score_breakdown

    def test_reason_mentions_provider(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_CHEAPEST)
        assert "gemini" in result.reason.lower()


# ---------------------------------------------------------------------------
# Fastest strategy
# ---------------------------------------------------------------------------


class TestFastestStrategy:
    def test_selects_fastest_model(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_FASTEST)
        # STATIC_LATENCY_MS: gemini-2.0-flash=650 (fastest registered model)
        assert result.selected_provider_id == "gemini"
        assert result.selected_model == "gemini-2.0-flash"

    def test_candidates_sorted_by_score_desc(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_FASTEST)
        scores = [c.score for c in result.candidates]
        assert scores == sorted(scores, reverse=True)

    def test_score_breakdown_has_latency_key(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_FASTEST)
        for c in result.candidates:
            assert "latency" in c.score_breakdown


# ---------------------------------------------------------------------------
# Quality strategy
# ---------------------------------------------------------------------------


class TestQualityStrategy:
    def test_selects_highest_quality_model(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_QUALITY)
        # gpt-4o quality=0.92 — highest
        assert result.selected_provider_id == "openai"
        assert result.selected_model == "gpt-4o"

    def test_candidates_sorted_by_score_desc(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_QUALITY)
        scores = [c.score for c in result.candidates]
        assert scores == sorted(scores, reverse=True)

    def test_score_breakdown_has_quality_key(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_QUALITY)
        for c in result.candidates:
            assert "quality" in c.score_breakdown


# ---------------------------------------------------------------------------
# Auto strategy
# ---------------------------------------------------------------------------


class TestAutoStrategy:
    def test_returns_routing_result(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_AUTO)
        assert result.strategy == STRATEGY_AUTO
        assert result.selected_provider_id
        assert result.selected_model

    def test_score_breakdown_has_all_dimensions(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_AUTO)
        for c in result.candidates:
            assert set(c.score_breakdown.keys()) == {"quality", "cost", "latency", "health"}

    def test_all_dimensions_between_0_and_1(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_AUTO)
        for c in result.candidates:
            for v in c.score_breakdown.values():
                assert 0.0 <= v <= 1.0, f"Score component {v} out of range"

    def test_candidates_sorted_by_score_desc(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_AUTO)
        scores = [c.score for c in result.candidates]
        assert scores == sorted(scores, reverse=True)

    def test_winner_has_highest_score(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_AUTO)
        winner_candidate = next(
            c for c in result.candidates
            if c.provider_id == result.selected_provider_id and c.model_id == result.selected_model
        )
        assert winner_candidate.score == result.candidates[0].score


# ---------------------------------------------------------------------------
# Manual strategy
# ---------------------------------------------------------------------------


class TestManualStrategy:
    def test_selects_requested_provider(self, svc: RouterService) -> None:
        result = svc.select("manual", manual_provider_id="anthropic")
        assert result.selected_provider_id == "anthropic"

    def test_strategy_field_is_manual(self, svc: RouterService) -> None:
        result = svc.select("manual", manual_provider_id="openai")
        assert result.strategy == "manual"

    def test_explicit_model_override(self, svc: RouterService) -> None:
        result = svc.select("manual", manual_provider_id="openai", manual_model_id="gpt-4o")
        assert result.selected_model == "gpt-4o"

    def test_fallback_to_default_model_when_no_override(self, svc: RouterService) -> None:
        result = svc.select("manual", manual_provider_id="gemini")
        # Should use the first model registered for gemini
        assert result.selected_model  # non-empty

    def test_all_candidates_present_for_inspector(self, svc: RouterService) -> None:
        result = svc.select("manual", manual_provider_id="openai")
        provider_ids = {c.provider_id for c in result.candidates}
        assert "openai" in provider_ids
        assert "anthropic" in provider_ids
        assert "gemini" in provider_ids

    def test_candidates_have_auto_score_breakdown(self, svc: RouterService) -> None:
        result = svc.select("manual", manual_provider_id="openai")
        for c in result.candidates:
            assert set(c.score_breakdown.keys()) == {"quality", "cost", "latency", "health"}

    def test_unknown_provider_raises_service_unavailable(self, svc: RouterService) -> None:
        with pytest.raises(ServiceUnavailableError):
            svc.select("manual", manual_provider_id="nonexistent-provider")

    def test_reason_mentions_manual(self, svc: RouterService) -> None:
        result = svc.select("manual", manual_provider_id="openai")
        assert "manual" in result.reason.lower()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_unknown_strategy_raises_bad_request(self, svc: RouterService) -> None:
        with pytest.raises(BadRequestError):
            svc.select("not_a_strategy")

    def test_empty_registry_raises_service_unavailable(self) -> None:
        empty_svc = RouterService(ProviderRegistry())
        with pytest.raises(ServiceUnavailableError):
            empty_svc.select(STRATEGY_AUTO)

    def test_single_candidate_all_strategies(self) -> None:
        tiny = _FakeProvider("tiny", [_make_model("tiny-model", 0.001, 0.002, 0.70, "tiny")])
        svc = RouterService(_make_registry(tiny))
        for strategy in [STRATEGY_AUTO, STRATEGY_CHEAPEST, STRATEGY_FASTEST, STRATEGY_QUALITY]:
            result = svc.select(strategy)
            assert result.selected_provider_id == "tiny"
            assert result.selected_model == "tiny-model"
            assert len(result.candidates) == 1

    def test_down_provider_excluded_from_auto(self) -> None:
        """A candidate whose model latency puts it first but health=DOWN should be skipped."""
        from app.services.router_service import ProviderCandidate, ScoredCandidate

        # Build a RouterService and monkey-patch _build_candidates to inject a DOWN candidate
        svc = RouterService(_make_registry(_OPENAI))
        original_build = svc._build_candidates

        def patched_build():
            candidates = original_build()
            # Mark all openai models as DOWN
            return [
                ProviderCandidate(
                    provider_id=c.provider_id,
                    model_id=c.model_id,
                    cost_per_1k=c.cost_per_1k,
                    latency_ms=c.latency_ms,
                    quality_score=c.quality_score,
                    health=STATUS_DOWN,
                    supports_streaming=c.supports_streaming,
                )
                for c in candidates
            ]

        svc._build_candidates = patched_build  # type: ignore[method-assign]

        with pytest.raises(ServiceUnavailableError):
            svc.select(STRATEGY_AUTO)

    def test_total_candidates_count(self, svc: RouterService) -> None:
        result = svc.select(STRATEGY_AUTO)
        # 3 providers × 2 models each = 6
        assert len(result.candidates) == 6
