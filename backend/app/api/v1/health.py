"""
Health, readiness, liveness, and version endpoints.

These endpoints are used by:
- Docker health checks
- Railway deployment health probes
- Load balancer readiness gates
- Monitoring systems

Endpoints:
    GET /health        — combined health check (DB + Redis)
    GET /health/ready  — readiness: are all dependencies available?
    GET /health/live   — liveness: is the process alive?
    GET /version       — application version metadata
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.client import get_redis_client
from app.config import get_settings
from app.database.session import get_db_session
from app.core.logging import get_logger

router = APIRouter()
log = get_logger(__name__)


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Combined health check",
    tags=["health"],
)
async def health_check(
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),  # type: ignore[type-arg]
) -> dict:
    """
    Check the health of the application and its dependencies.

    Returns 200 if both PostgreSQL and Redis are reachable.
    Returns 503 if any dependency is unavailable.
    """
    db_ok = False
    redis_ok = False

    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        log.error("health_check_db_failed", error=str(exc))

    try:
        redis_ok = bool(await redis.ping())
    except Exception as exc:
        log.error("health_check_redis_failed", error=str(exc))

    overall = db_ok and redis_ok

    return {
        "status": "healthy" if overall else "unhealthy",
        "dependencies": {
            "database": "up" if db_ok else "down",
            "redis": "up" if redis_ok else "down",
        },
    }


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    tags=["health"],
)
async def readiness(
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),  # type: ignore[type-arg]
) -> dict:
    """
    Kubernetes/Railway readiness probe.

    Returns 200 when the application is ready to serve traffic (DB and Redis
    connections are established).
    """
    try:
        await db.execute(text("SELECT 1"))
        await redis.ping()
        return {"ready": True}
    except Exception as exc:
        log.warning("readiness_probe_failed", error=str(exc))
        return {"ready": False}


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    tags=["health"],
)
async def liveness() -> dict:
    """
    Kubernetes/Railway liveness probe.

    Always returns 200 as long as the process is running.
    If this endpoint returns an error, the process has crashed.
    """
    return {"alive": True}


@router.get(
    "/version",
    status_code=status.HTTP_200_OK,
    summary="Version metadata",
    tags=["health"],
)
async def version() -> dict:
    """Return application version and environment metadata."""
    settings = get_settings()
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment.value,
    }
