"""API key management service — Phase 1 stub."""

from __future__ import annotations

# TODO(phase-2): Implement APIKeyService with:
#   - create(user_id, name, expires_at) -> APIKeyCreatedResponse
#   - list(user_id) -> APIKeysListResponse
#   - revoke(user_id, key_id) -> None
#   - verify(raw_key) -> User | None   (for API key auth path)
#   Key format: vk-{32 url-safe random chars}. Store prefix + bcrypt hash only.
