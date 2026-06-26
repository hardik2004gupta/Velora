"""Request history endpoints — Phase 1 stubs."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="List request history")
async def list_requests() -> dict:
    """TODO(phase-2): Return paginated request history with filters."""
    return {"message": "Not implemented — Phase 2"}


@router.get("/{request_id}", summary="Get request detail")
async def get_request(request_id: str) -> dict:
    """TODO(phase-2): Return full request detail including routing decision."""
    return {"message": "Not implemented — Phase 2"}
