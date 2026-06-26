"""API key service — create, list, revoke, rotate, and verify keys."""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.core.security import hash_api_key, verify_api_key
from app.models.api_key import APIKey
from app.models.organization import Organization
from app.repositories.api_key_repository import APIKeyRepository
from app.schemas.api_key import CreateAPIKeyRequest, CreateAPIKeyResponse, RotateAPIKeyResponse

log = get_logger(__name__)

_KEY_PREFIX_LEN = 8


def _generate_raw_key() -> str:
    """Return a new ``vk-`` prefixed API key. The full key is shown once."""
    return f"vk-{secrets.token_urlsafe(32)}"


class APIKeyService:
    def __init__(
        self,
        db: AsyncSession,
        api_key_repo: APIKeyRepository | None = None,
    ) -> None:
        self._db = db
        self._repo = api_key_repo or APIKeyRepository(db)

    async def create(
        self,
        org: Organization,
        payload: CreateAPIKeyRequest,
        *,
        request_id: str = "",
    ) -> CreateAPIKeyResponse:
        raw_key = _generate_raw_key()
        prefix = raw_key[:_KEY_PREFIX_LEN]
        hashed = hash_api_key(raw_key)
        expires_at: datetime | None = None
        if payload.expires_in_days is not None:
            expires_at = datetime.now(UTC) + timedelta(days=payload.expires_in_days)

        key = await self._repo.create(
            org_id=org.id,
            name=payload.name,
            key_prefix=prefix,
            hashed_key=hashed,
            role=payload.role,
            expires_at=expires_at,
        )
        log.info(
            "api_key_created",
            org_id=str(org.id),
            key_id=str(key.id),
            name=payload.name,
            request_id=request_id,
        )
        return CreateAPIKeyResponse(
            id=str(key.id),
            name=key.name,
            key_prefix=key.key_prefix,
            role=key.role,
            expires_at=key.expires_at,
            created_at=key.created_at,
            full_key=raw_key,
        )

    async def list_for_org(self, org: Organization) -> list[APIKey]:
        return await self._repo.get_active_by_org(org.id)

    async def revoke(
        self,
        org: Organization,
        key_id: uuid.UUID,
        *,
        request_id: str = "",
    ) -> None:
        key = await self._repo.get(key_id)
        if key is None or key.organization_id != org.id:
            raise NotFoundError("API key not found.")
        if key.revoked:
            return
        await self._repo.revoke(key)
        log.info(
            "api_key_revoked",
            org_id=str(org.id),
            key_id=str(key_id),
            request_id=request_id,
        )

    async def rotate(
        self,
        org: Organization,
        key_id: uuid.UUID,
        *,
        request_id: str = "",
    ) -> RotateAPIKeyResponse:
        """
        Revoke the existing key and issue a replacement with the same metadata.

        The new key is returned in full exactly once.
        """
        old_key = await self._repo.get(key_id)
        if old_key is None or old_key.organization_id != org.id:
            raise NotFoundError("API key not found.")

        await self._repo.revoke(old_key)

        raw_key = _generate_raw_key()
        prefix = raw_key[:_KEY_PREFIX_LEN]
        hashed = hash_api_key(raw_key)

        new_key = await self._repo.create(
            org_id=org.id,
            name=old_key.name,
            key_prefix=prefix,
            hashed_key=hashed,
            role=old_key.role,
            expires_at=old_key.expires_at,
        )
        log.info(
            "api_key_rotated",
            org_id=str(org.id),
            old_key_id=str(key_id),
            new_key_id=str(new_key.id),
            request_id=request_id,
        )
        return RotateAPIKeyResponse(
            id=str(new_key.id),
            name=new_key.name,
            key_prefix=new_key.key_prefix,
            role=new_key.role,
            expires_at=new_key.expires_at,
            created_at=new_key.created_at,
            new_key=raw_key,
        )

    async def verify(self, raw_key: str) -> APIKey | None:
        """
        Validate an inbound API key and return the APIKey row, or None.

        Also updates ``last_used_at`` on a successful match.
        """
        prefix = raw_key[:_KEY_PREFIX_LEN]
        candidates = await self._repo.get_by_prefix(prefix)
        for candidate in candidates:
            if verify_api_key(raw_key, candidate.hashed_key):
                await self._repo.touch(candidate)
                return candidate
        return None
