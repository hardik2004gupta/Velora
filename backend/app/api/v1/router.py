"""
API v1 aggregate router.

All sub-routers are included here and mounted on the FastAPI app via::

    app.include_router(v1_router, prefix="/api/v1")
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    analytics,
    auth,
    cache,
    chat,
    health,
    providers,
    requests,
    settings,
    user_keys,
)

v1_router = APIRouter()

v1_router.include_router(health.router, tags=["health"])
v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
v1_router.include_router(chat.router, prefix="/chat", tags=["chat"])
v1_router.include_router(requests.router, prefix="/requests", tags=["requests"])
v1_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
v1_router.include_router(providers.router, prefix="/providers", tags=["providers"])
v1_router.include_router(user_keys.router, prefix="/api-keys", tags=["api-keys"])
v1_router.include_router(settings.router, prefix="/settings", tags=["settings"])
v1_router.include_router(admin.router, prefix="/admin", tags=["admin"])
v1_router.include_router(cache.router, prefix="/cache", tags=["cache"])
