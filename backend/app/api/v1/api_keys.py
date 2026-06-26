"""API key management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_org, require_role
from app.core.rbac import Role
from app.models.membership import Membership
from app.models.organization import Organization
from app.schemas.api_key import (
    APIKeyResponse,
    APIKeysListResponse,
    CreateAPIKeyRequest,
    CreateAPIKeyResponse,
    RotateAPIKeyResponse,
)
from app.services.api_key_service import APIKeyService

router = APIRouter()


@router.get("", response_model=APIKeysListResponse, summary="List API keys for an org")
async def list_keys(
    request: Request,
    org_and_membership: tuple[Organization, Membership] = Depends(get_current_org),
    db: AsyncSession = Depends(get_db_session),
) -> APIKeysListResponse:
    org, _ = org_and_membership
    service = APIKeyService(db)
    keys = await service.list_for_org(org)
    items = [
        APIKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            role=k.role,
            last_used_at=k.last_used_at,
            expires_at=k.expires_at,
            revoked=k.revoked,
            is_active=k.is_active,
            created_at=k.created_at,
        )
        for k in keys
    ]
    return APIKeysListResponse(items=items, total=len(items))


@router.post("", status_code=201, response_model=CreateAPIKeyResponse, summary="Create API key")
async def create_key(
    payload: CreateAPIKeyRequest,
    request: Request,
    org_and_membership: tuple[Organization, Membership] = Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> CreateAPIKeyResponse:
    org, _ = org_and_membership
    service = APIKeyService(db)
    return await service.create(
        org,
        payload,
        request_id=getattr(request.state, "request_id", ""),
    )


@router.delete("/{key_id}", status_code=204, summary="Revoke API key")
async def revoke_key(
    key_id: uuid.UUID,
    request: Request,
    org_and_membership: tuple[Organization, Membership] = Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    org, _ = org_and_membership
    service = APIKeyService(db)
    await service.revoke(org, key_id, request_id=getattr(request.state, "request_id", ""))


@router.post("/{key_id}/rotate", response_model=RotateAPIKeyResponse, summary="Rotate API key")
async def rotate_key(
    key_id: uuid.UUID,
    request: Request,
    org_and_membership: tuple[Organization, Membership] = Depends(require_role(Role.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> RotateAPIKeyResponse:
    org, _ = org_and_membership
    service = APIKeyService(db)
    return await service.rotate(org, key_id, request_id=getattr(request.state, "request_id", ""))
