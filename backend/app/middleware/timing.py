"""
Request timing middleware.

Measures total wall-clock time for every request and emits a structured log
event.  Also sets the ``X-Process-Time-Ms`` response header for debugging.
"""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.logging import get_logger

log = get_logger(__name__)

PROCESS_TIME_HEADER = "X-Process-Time-Ms"


class TimingMiddleware(BaseHTTPMiddleware):
    """Measure and log the wall-clock time for every HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        response.headers[PROCESS_TIME_HEADER] = str(duration_ms)

        log.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        return response
