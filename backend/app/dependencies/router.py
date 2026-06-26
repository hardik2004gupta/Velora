"""FastAPI dependency for the RouterService."""

from __future__ import annotations

from app.providers.registry import get_registry
from app.services.router_service import RouterService


def get_router_service() -> RouterService:
    """Return a RouterService bound to the global provider registry."""
    return RouterService(get_registry())
