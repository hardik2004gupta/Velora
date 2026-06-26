"""Analytics endpoints — Phase 1 stubs."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/overview", summary="Analytics overview")
async def overview() -> dict:
    return {"message": "Not implemented — Phase 2"}


@router.get("/cost-over-time", summary="Daily cost series")
async def cost_over_time() -> dict:
    return {"message": "Not implemented — Phase 2"}


@router.get("/latency-over-time", summary="Latency by provider over time")
async def latency_over_time() -> dict:
    return {"message": "Not implemented — Phase 2"}


@router.get("/provider-distribution", summary="Provider usage breakdown")
async def provider_distribution() -> dict:
    return {"message": "Not implemented — Phase 2"}
