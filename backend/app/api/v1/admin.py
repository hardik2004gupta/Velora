"""Admin endpoints — Phase 1 stubs."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/users", summary="List all users (admin only)")
async def list_users() -> dict:
    return {"message": "Not implemented — Phase 2"}


@router.get("/stats", summary="Platform-wide stats (admin only)")
async def platform_stats() -> dict:
    return {"message": "Not implemented — Phase 2"}


@router.patch("/users/{user_id}/status", summary="Toggle user active status")
async def update_user_status(user_id: str) -> dict:
    return {"message": "Not implemented — Phase 2"}
