"""Personal API key management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user_key import UserAPIKeyCreate, UserAPIKeyCreateResponse, UserAPIKeyResponse
from app.services.user_key_service import UserKeyService

router = APIRouter()


@router.get("", response_model=list[UserAPIKeyResponse], summary="List personal API keys")
async def list_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[UserAPIKeyResponse]:
    svc = UserKeyService(db)
    keys = await svc.list_for_user(user.id)
    return [
        UserAPIKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            last_used_at=k.last_used_at,
            is_active=k.is_active,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.post(
    "",
    response_model=UserAPIKeyCreateResponse,
    status_code=201,
    summary="Create a personal API key (key shown once)",
)
async def create_key(
    body: UserAPIKeyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> UserAPIKeyCreateResponse:
    svc = UserKeyService(db)
    key_model, plain_key = await svc.create(user.id, body.name)
    await db.commit()
    return UserAPIKeyCreateResponse(
        id=key_model.id,
        name=key_model.name,
        key_prefix=key_model.key_prefix,
        last_used_at=key_model.last_used_at,
        is_active=key_model.is_active,
        created_at=key_model.created_at,
        key=plain_key,
    )


@router.delete(
    "/{key_id}",
    summary="Revoke a personal API key",
)
async def revoke_key(
    key_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Response:
    svc = UserKeyService(db)
    await svc.revoke(key_id, user.id)
    await db.commit()
    return Response(status_code=204)
