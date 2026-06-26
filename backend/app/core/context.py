"""
Request context.

A ``RequestContext`` is populated per-request by the auth dependencies and
stored on ``request.state.context``.  It provides a single place to read
the authenticated identity, organization, and request metadata from any
service or route handler — without threading or globals.

Usage (inside a route or service that received the context via DI)::

    from app.core.context import RequestContext

    async def some_route(ctx: RequestContext = Depends(get_request_context)):
        log = ctx.logger.bind(action="do_something")
        log.info("starting")
        ...
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from app.models.api_key import APIKey
    from app.models.organization import Organization
    from app.models.user import User


@dataclass
class RequestContext:
    """
    Immutable-ish snapshot of all request-scoped identity and metadata.

    Fields are populated incrementally by the DI chain:
    1. ``RequestIDMiddleware`` sets ``request_id``.
    2. Auth dependencies set ``user``, ``organization``, ``api_key``.
    3. ``logger`` is pre-bound with all of the above for structured logging.
    """

    # Identity — set by auth layer
    user: User | None = None
    organization: Organization | None = None
    api_key: APIKey | None = None

    # Request metadata — set by middleware
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ip_address: str | None = None
    user_agent: str | None = None

    # Timing
    started_at: float = field(default_factory=time.monotonic)

    # Logger — re-bound after identity is loaded
    _logger: Any = field(default=None, repr=False)

    @property
    def elapsed_ms(self) -> float:
        """Elapsed milliseconds since this context was created."""
        return (time.monotonic() - self.started_at) * 1000

    @property
    def user_id(self) -> str | None:
        """Convenience: return the authenticated user's ID as a string, or None."""
        return str(self.user.id) if self.user else None

    @property
    def org_id(self) -> str | None:
        """Convenience: return the active organization's ID as a string, or None."""
        return str(self.organization.id) if self.organization else None

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Return a structlog logger pre-bound with request context fields."""
        if self._logger is None:
            self._logger = structlog.get_logger(__name__).bind(
                request_id=self.request_id,
                trace_id=self.trace_id,
                user_id=self.user_id,
                org_id=self.org_id,
            )
        return self._logger  # type: ignore[return-value]

    def bind_identity(self) -> None:
        """
        Re-bind the structlog context variables after identity is loaded.

        Call this once the user/org are populated so all subsequent log
        statements from this request include the identity fields.
        """
        import structlog as _structlog
        _structlog.contextvars.bind_contextvars(
            request_id=self.request_id,
            user_id=self.user_id,
            org_id=self.org_id,
        )
        # Reset cached logger so it picks up the new bindings
        self._logger = None
