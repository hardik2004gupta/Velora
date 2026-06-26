"""
Authentication endpoints — Phase 1 stubs.

POST /auth/register  — create account
POST /auth/login     — get JWT token
GET  /auth/me        — current user profile

Full implementation in Phase 2.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post("/register", status_code=201, summary="Register a new account")
async def register() -> dict:
    """TODO(phase-2): Implement user registration."""
    return {"message": "Not implemented — Phase 2"}


@router.post("/login", summary="Login and receive a JWT token")
async def login() -> dict:
    """TODO(phase-2): Implement login."""
    return {"message": "Not implemented — Phase 2"}


@router.get("/me", summary="Get current user profile")
async def me() -> dict:
    """TODO(phase-2): Implement /me endpoint."""
    return {"message": "Not implemented — Phase 2"}
