"""Provider status endpoints — Phase 1 stubs."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/status", summary="Provider health status")
async def provider_status() -> dict:
    return {"message": "Not implemented — Phase 2"}
