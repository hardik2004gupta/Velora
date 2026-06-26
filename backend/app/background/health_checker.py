"""
Background health checker — Phase 1 stub.

Periodically pings each registered LLM provider and records the result in
``provider_status``.  Runs as an APScheduler job started in the lifespan handler.

Full implementation in Phase 2.
"""

from __future__ import annotations

from app.core.logging import get_logger

log = get_logger(__name__)


async def run_health_checks() -> None:
    """
    Execute a health check against every registered provider.

    Called by APScheduler on ``HEALTH_CHECK_INTERVAL_SECONDS`` interval.
    Phase 1: logs a placeholder message.
    Phase 2: calls HealthService.check_all_providers() and persists results.
    """
    log.info("health_check_run", status="placeholder — implemented in Phase 2")
    # TODO(phase-2): Implement full health check loop:
    #   1. Iterate ProviderRegistry.get_all()
    #   2. Call provider.health_check() with timeout
    #   3. Measure latency
    #   4. Update provider_status table
    #   5. Update Redis latency rolling average
