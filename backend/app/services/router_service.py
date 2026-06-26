"""
Router service — deterministic, rule-based provider selection.

All scoring is rule-based (no ML) so every decision is fully explainable
by the Routing Decision Inspector.

Architecture:
  RouterService.select() → RoutingResult
    ├── _build_candidates()    Enumerate all (provider, model) pairs
    ├── _score_*()             Score each pair for the chosen strategy
    └── _explain()             Build a human-readable reason string

The router NEVER calls provider APIs.  It only evaluates metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.constants import (
    AUTO_WEIGHT_COST,
    AUTO_WEIGHT_HEALTH,
    AUTO_WEIGHT_LATENCY,
    AUTO_WEIGHT_QUALITY,
    STATIC_LATENCY_MS,
    STATUS_DOWN,
    STATUS_HEALTHY,
    STRATEGY_AUTO,
    STRATEGY_CHEAPEST,
    STRATEGY_FASTEST,
    STRATEGY_QUALITY,
)
from app.core.exceptions import BadRequestError, ServiceUnavailableError
from app.core.logging import get_logger
from app.providers.registry import ProviderRegistry

log = get_logger(__name__)

_EPSILON = 1e-9  # prevent divide-by-zero in normalisation

ALL_ROUTING_STRATEGIES = {STRATEGY_AUTO, STRATEGY_CHEAPEST, STRATEGY_FASTEST, STRATEGY_QUALITY, "manual"}


# ---------------------------------------------------------------------------
# Data structures (internal — never leak to API layer directly)
# ---------------------------------------------------------------------------


@dataclass
class ProviderCandidate:
    """Metadata snapshot for one (provider, model) pair used by scoring."""

    provider_id: str
    model_id: str
    cost_per_1k: float         # (input_cost + output_cost) / 2 in USD
    latency_ms: int            # static TTFT estimate
    quality_score: float       # 0.0–1.0 benchmark aggregate
    health: str                # healthy | down
    supports_streaming: bool


@dataclass
class ScoredCandidate:
    """A candidate with its computed routing score."""

    provider_id: str
    model_id: str
    cost_per_1k: float
    latency_ms: int
    quality_score: float
    health: str
    supports_streaming: bool
    score: float
    score_breakdown: dict[str, float] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return self.health != STATUS_DOWN


@dataclass
class RoutingResult:
    """The complete output of the routing engine for one request."""

    strategy: str
    selected_provider_id: str
    selected_model: str
    reason: str
    candidates: list[ScoredCandidate]  # sorted best → worst


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------


def _normalise(values: list[float]) -> list[float]:
    """Min-max normalise *values* to [0, 1].  Safe for single-element lists."""
    mn, mx = min(values), max(values)
    rng = mx - mn + _EPSILON
    return [(v - mn) / rng for v in values]


# ---------------------------------------------------------------------------
# RouterService
# ---------------------------------------------------------------------------


class RouterService:
    """
    Stateless routing engine.

    Instantiate once per request via ``get_router_service()`` dependency.
    """

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def select(
        self,
        strategy: str,
        manual_provider_id: str | None = None,
        manual_model_id: str | None = None,
    ) -> RoutingResult:
        """
        Select the best (provider, model) for the given *strategy*.

        Args:
            strategy:           One of auto | cheapest | fastest | quality | manual.
            manual_provider_id: Required when strategy == "manual".
            manual_model_id:    Optional explicit model override (manual mode only).

        Returns:
            A ``RoutingResult`` with the winner and full scored candidate list.

        Raises:
            BadRequestError:         Unknown strategy.
            ServiceUnavailableError: No providers registered, or manual provider absent.
        """
        if strategy not in ALL_ROUTING_STRATEGIES:
            raise BadRequestError(
                f"Unknown routing strategy '{strategy}'. "
                f"Valid: {sorted(ALL_ROUTING_STRATEGIES)}"
            )

        candidates = self._build_candidates()
        if not candidates:
            raise ServiceUnavailableError("No LLM providers are configured.")

        if strategy == "manual" or manual_provider_id:
            return self._select_manual(candidates, manual_provider_id or "", manual_model_id)

        healthy = [c for c in candidates if c.is_healthy]
        if not healthy:
            raise ServiceUnavailableError("All providers are currently unavailable.")

        if strategy == STRATEGY_CHEAPEST:
            return self._route_cheapest(candidates)
        if strategy == STRATEGY_FASTEST:
            return self._route_fastest(candidates)
        if strategy == STRATEGY_QUALITY:
            return self._route_quality(candidates)
        return self._route_auto(candidates)  # STRATEGY_AUTO and any unknown

    # -------------------------------------------------------------------------
    # Candidate construction
    # -------------------------------------------------------------------------

    def _build_candidates(self) -> list[ProviderCandidate]:
        """Build one ProviderCandidate per registered (provider, model) pair."""
        candidates: list[ProviderCandidate] = []
        for provider in self._registry.get_all():
            pid = provider.get_id()
            for m in provider.get_available_models():
                avg_cost = (m.cost_input_per_1k + m.cost_output_per_1k) / 2
                candidates.append(
                    ProviderCandidate(
                        provider_id=pid,
                        model_id=m.model_id,
                        cost_per_1k=avg_cost,
                        latency_ms=STATIC_LATENCY_MS.get(m.model_id, 1000),
                        quality_score=m.quality_score,
                        health=STATUS_HEALTHY,  # no background polling yet; assume healthy
                        supports_streaming=m.supports_streaming,
                    )
                )
        return candidates

    # -------------------------------------------------------------------------
    # Scoring functions
    # -------------------------------------------------------------------------

    def _score_cheapest(self, candidates: list[ProviderCandidate]) -> list[ScoredCandidate]:
        """Score = 1 - normalised_cost  (lower cost → higher score)."""
        costs = [c.cost_per_1k for c in candidates]
        norm = _normalise(costs)
        return [
            ScoredCandidate(
                **vars(c),
                score=round(1.0 - norm[i], 4),
                score_breakdown={"cost": round(1.0 - norm[i], 4)},
            )
            for i, c in enumerate(candidates)
        ]

    def _score_fastest(self, candidates: list[ProviderCandidate]) -> list[ScoredCandidate]:
        """Score = 1 - normalised_latency  (lower latency → higher score)."""
        latencies = [float(c.latency_ms) for c in candidates]
        norm = _normalise(latencies)
        return [
            ScoredCandidate(
                **vars(c),
                score=round(1.0 - norm[i], 4),
                score_breakdown={"latency": round(1.0 - norm[i], 4)},
            )
            for i, c in enumerate(candidates)
        ]

    def _score_quality(self, candidates: list[ProviderCandidate]) -> list[ScoredCandidate]:
        """Score = quality_score  (already in [0,1])."""
        return [
            ScoredCandidate(
                **vars(c),
                score=round(c.quality_score, 4),
                score_breakdown={"quality": round(c.quality_score, 4)},
            )
            for c in candidates
        ]

    def _score_auto(self, candidates: list[ProviderCandidate]) -> list[ScoredCandidate]:
        """Weighted composite: quality·0.35 + cost·0.30 + latency·0.25 + health·0.10."""
        costs = [c.cost_per_1k for c in candidates]
        latencies = [float(c.latency_ms) for c in candidates]
        cost_norm = _normalise(costs)
        lat_norm = _normalise(latencies)

        scored: list[ScoredCandidate] = []
        for i, c in enumerate(candidates):
            health_score = 1.0 if c.health == STATUS_HEALTHY else 0.0
            cost_score = 1.0 - cost_norm[i]
            lat_score = 1.0 - lat_norm[i]
            q_score = c.quality_score

            total = round(
                AUTO_WEIGHT_QUALITY * q_score
                + AUTO_WEIGHT_COST * cost_score
                + AUTO_WEIGHT_LATENCY * lat_score
                + AUTO_WEIGHT_HEALTH * health_score,
                4,
            )
            scored.append(
                ScoredCandidate(
                    **vars(c),
                    score=total,
                    score_breakdown={
                        "quality": round(q_score, 4),
                        "cost": round(cost_score, 4),
                        "latency": round(lat_score, 4),
                        "health": round(health_score, 4),
                    },
                )
            )
        return scored

    # -------------------------------------------------------------------------
    # Strategy implementations
    # -------------------------------------------------------------------------

    def _route_cheapest(self, candidates: list[ProviderCandidate]) -> RoutingResult:
        scored = self._score_cheapest(candidates)
        winner = max((s for s in scored if s.is_healthy), key=lambda s: s.score)
        return RoutingResult(
            strategy=STRATEGY_CHEAPEST,
            selected_provider_id=winner.provider_id,
            selected_model=winner.model_id,
            reason=(
                f"Selected {winner.provider_id}/{winner.model_id} as the cheapest available "
                f"option at ${winner.cost_per_1k:.5f} per 1K tokens."
            ),
            candidates=sorted(scored, key=lambda s: s.score, reverse=True),
        )

    def _route_fastest(self, candidates: list[ProviderCandidate]) -> RoutingResult:
        scored = self._score_fastest(candidates)
        winner = max((s for s in scored if s.is_healthy), key=lambda s: s.score)
        return RoutingResult(
            strategy=STRATEGY_FASTEST,
            selected_provider_id=winner.provider_id,
            selected_model=winner.model_id,
            reason=(
                f"Selected {winner.provider_id}/{winner.model_id} with the lowest estimated "
                f"latency of {winner.latency_ms}ms."
            ),
            candidates=sorted(scored, key=lambda s: s.score, reverse=True),
        )

    def _route_quality(self, candidates: list[ProviderCandidate]) -> RoutingResult:
        scored = self._score_quality(candidates)
        winner = max((s for s in scored if s.is_healthy), key=lambda s: s.score)
        return RoutingResult(
            strategy=STRATEGY_QUALITY,
            selected_provider_id=winner.provider_id,
            selected_model=winner.model_id,
            reason=(
                f"Selected {winner.provider_id}/{winner.model_id} with the highest "
                f"quality score ({winner.quality_score:.0%})."
            ),
            candidates=sorted(scored, key=lambda s: s.score, reverse=True),
        )

    def _route_auto(self, candidates: list[ProviderCandidate]) -> RoutingResult:
        scored = self._score_auto(candidates)
        winner = max((s for s in scored if s.is_healthy), key=lambda s: s.score)
        bd = winner.score_breakdown
        return RoutingResult(
            strategy=STRATEGY_AUTO,
            selected_provider_id=winner.provider_id,
            selected_model=winner.model_id,
            reason=(
                f"Selected {winner.provider_id}/{winner.model_id} with the highest composite "
                f"score ({winner.score:.2f}) — quality {bd.get('quality', 0):.0%}, "
                f"cost rank {bd.get('cost', 0):.0%}, "
                f"latency rank {bd.get('latency', 0):.0%}."
            ),
            candidates=sorted(scored, key=lambda s: s.score, reverse=True),
        )

    def _select_manual(
        self,
        candidates: list[ProviderCandidate],
        provider_id: str,
        model_id: str | None,
    ) -> RoutingResult:
        match = next((c for c in candidates if c.provider_id == provider_id), None)
        if match is None:
            available = sorted({c.provider_id for c in candidates})
            raise ServiceUnavailableError(
                f"Provider '{provider_id}' is not available. "
                f"Registered: {available}"
            )

        # Score all candidates with auto weights so the inspector can show comparisons
        scored_all = self._score_auto(candidates)
        effective_model = model_id or match.model_id

        return RoutingResult(
            strategy="manual",
            selected_provider_id=provider_id,
            selected_model=effective_model,
            reason=(
                f"Provider '{provider_id}' was selected manually. "
                f"Automatic routing was bypassed."
            ),
            candidates=sorted(scored_all, key=lambda s: s.score, reverse=True),
        )
