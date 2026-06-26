"""
FastAPI application factory.

Creates and configures the ASGI application.  All startup / shutdown logic
lives in the ``lifespan`` context manager so resources are always cleaned up.

Usage::

    uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.router import v1_router
from app.cache import client as cache_client
from app.config import get_settings
from app.core.exceptions import HTTPError, RateLimitExceededError
from app.core.logging import configure_logging, get_logger
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.timing import TimingMiddleware
from app.providers.registry import get_registry
from app.telemetry import setup_telemetry
from app.utils.response import error_response, validation_error_response

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup + shutdown
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application-level resources.

    Everything before ``yield`` runs at startup; everything after runs at
    shutdown.  FastAPI guarantees shutdown even if a startup step raises.
    """
    settings = get_settings()

    # 1. Configure logging first so every subsequent log is structured
    configure_logging(
        log_level=settings.log_level,
        json_logs=(settings.log_format.value == "json"),
    )
    log.info("velora_starting", version=settings.app_version, env=settings.environment.value)

    # 2. Telemetry (no-op unless OTEL_ENABLED=true)
    setup_telemetry()

    # 3. Redis connection pool
    cache_client.setup()

    # 4. Provider registry — register adapters for configured API keys
    registry = get_registry()
    registry.setup_from_settings()

    log.info("velora_ready", providers=registry.provider_ids())

    yield  # ── application is serving requests ──

    # Shutdown
    log.info("velora_shutting_down")
    await cache_client.teardown()


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Velora API",
        description="Production-Inspired Multi-Provider AI Inference Platform",
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # --- Middleware (applied last-registered first) -------------------------
    # Order: RequestID → Security → Timing → Gzip → CORS
    # RequestID must be outermost so all logs include the request_id.

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-API-Key"],
        expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
    )

    # --- Exception handlers -------------------------------------------------

    @app.exception_handler(HTTPError)
    async def http_error_handler(request: Request, exc: HTTPError) -> ORJSONResponse:
        log.warning(
            "http_error",
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
        )
        headers = None
        if isinstance(exc, RateLimitExceededError):
            headers = {"Retry-After": str(exc.retry_after_seconds)}
        return error_response(exc, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> ORJSONResponse:
        log.warning("validation_error", errors=exc.errors())
        return validation_error_response(exc.errors())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> ORJSONResponse:
        log.error("unhandled_exception", error=str(exc), exc_info=True)
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                    "details": {},
                }
            },
        )

    # --- Routes -------------------------------------------------------------

    app.include_router(v1_router, prefix="/api/v1")

    return app


# Module-level app instance — used by uvicorn
app: FastAPI = create_app()
