"""User settings endpoints — Phase 1 stubs."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="Get user settings")
async def get_settings_route() -> dict:
    return {"message": "Not implemented — Phase 2"}


@router.patch("", summary="Update user settings")
async def update_settings() -> dict:
    return {"message": "Not implemented — Phase 2"}
