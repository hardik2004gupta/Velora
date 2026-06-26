"""API key management endpoints — Phase 1 stubs."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="List API keys")
async def list_keys() -> dict:
    return {"message": "Not implemented — Phase 2"}


@router.post("", status_code=201, summary="Create API key")
async def create_key() -> dict:
    return {"message": "Not implemented — Phase 2"}


@router.delete("/{key_id}", status_code=204, summary="Revoke API key")
async def revoke_key(key_id: str) -> None:
    return None  # 204 No Content
