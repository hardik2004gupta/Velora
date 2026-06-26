"""
Provider health service — Phase 1 stub.

Runs lightweight HTTP checks against each provider and records results.
Full implementation in Phase 2.
"""

from __future__ import annotations

# TODO(phase-2): Implement HealthService with:
#   - check_all_providers() -> list[ProviderStatusResponse]
#   - check_provider(provider_id) -> ProviderStatusResponse
#   - update_provider_status(provider_id, status, latency_ms) -> None
#   Called by the APScheduler background task every HEALTH_CHECK_INTERVAL_SECONDS.
