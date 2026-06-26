"""Chat completions endpoint — Phase 1 stub."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post("/completions", summary="Submit a chat completion request")
async def chat_completions() -> dict:
    """TODO(phase-2): Implement streaming chat completions with routing."""
    return {"message": "Not implemented — Phase 2"}
