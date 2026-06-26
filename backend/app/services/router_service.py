"""
Router service — Phase 1 stub.

Implements deterministic provider selection for all four routing strategies.
Full implementation in Phase 2.

Architecture note: All scoring is rule-based (no ML).  This enables the
Routing Decision Inspector — every decision is fully explainable.
"""

from __future__ import annotations

# TODO(phase-2): Implement RouterService with:
#   - select_provider(strategy, available_providers) -> RoutingDecision
#   - _score_cheapest(candidates) -> list[ScoredCandidate]
#   - _score_fastest(candidates) -> list[ScoredCandidate]
#   - _score_quality(candidates) -> list[ScoredCandidate]
#   - _score_auto(candidates) -> list[ScoredCandidate]
#
# Scoring weights (from constants.py):
#   auto: quality=0.35, cost=0.30, latency=0.25, health=0.10
