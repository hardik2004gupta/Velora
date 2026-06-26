"""API key repository — Phase 1 stub."""

from __future__ import annotations

from app.models.api_key import APIKey
from app.repositories.base import BaseRepository


class APIKeyRepository(BaseRepository[APIKey]):
    """Data access for the api_keys table."""

    model = APIKey

    # TODO(phase-2): Add domain-specific queries:
    #   - get_active_by_user(user_id) -> list[APIKey]
    #   - get_by_prefix(key_prefix) -> list[APIKey]  (for key lookup)
    #   - update_last_used(key_id) -> None
