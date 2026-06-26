"""
Velora exception hierarchy.

All application exceptions inherit from ``VeloraError``.  HTTP-facing
exceptions carry a ``status_code`` and a ``error_code`` string that the
global exception handler serializes into the standard API error shape::

    {
        "error": {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "You have exceeded the rate limit of 20 requests/minute.",
            "details": {}
        }
    }
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any


class VeloraError(Exception):
    """Base class for all Velora application exceptions."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, Any] = details or {}


# ---------------------------------------------------------------------------
# HTTP-facing exceptions (carry a status code)
# ---------------------------------------------------------------------------


class HTTPError(VeloraError):
    """Exception that maps directly to an HTTP response."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_SERVER_ERROR"

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        *,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message, details)
        if error_code is not None:
            self.error_code = error_code


# --- 400 Bad Request ---------------------------------------------------------


class ValidationError(HTTPError):
    """Request payload failed validation."""

    status_code = HTTPStatus.BAD_REQUEST
    error_code = "VALIDATION_ERROR"


class BadRequestError(HTTPError):
    """Generic bad request."""

    status_code = HTTPStatus.BAD_REQUEST
    error_code = "BAD_REQUEST"


# --- 401 Unauthorized --------------------------------------------------------


class AuthenticationError(HTTPError):
    """Missing or invalid credentials."""

    status_code = HTTPStatus.UNAUTHORIZED
    error_code = "AUTHENTICATION_FAILED"


class InvalidTokenError(AuthenticationError):
    """JWT is malformed, expired, or has an invalid signature."""

    error_code = "INVALID_TOKEN"


class ExpiredTokenError(AuthenticationError):
    """JWT access token has expired."""

    error_code = "TOKEN_EXPIRED"


# --- 403 Forbidden -----------------------------------------------------------


class PermissionDeniedError(HTTPError):
    """Authenticated user lacks the required permission."""

    status_code = HTTPStatus.FORBIDDEN
    error_code = "PERMISSION_DENIED"


class AdminRequiredError(PermissionDeniedError):
    """Admin-only endpoint accessed by a non-admin user."""

    error_code = "ADMIN_REQUIRED"


# --- 404 Not Found -----------------------------------------------------------


class NotFoundError(HTTPError):
    """Requested resource does not exist."""

    status_code = HTTPStatus.NOT_FOUND
    error_code = "NOT_FOUND"


class UserNotFoundError(NotFoundError):
    """User with the given identifier does not exist."""

    error_code = "USER_NOT_FOUND"


class RequestNotFoundError(NotFoundError):
    """Inference request with the given ID does not exist."""

    error_code = "REQUEST_NOT_FOUND"


class APIKeyNotFoundError(NotFoundError):
    """API key with the given ID does not exist."""

    error_code = "API_KEY_NOT_FOUND"


# --- 409 Conflict ------------------------------------------------------------


class ConflictError(HTTPError):
    """Resource already exists or state conflict."""

    status_code = HTTPStatus.CONFLICT
    error_code = "CONFLICT"


class EmailAlreadyExistsError(ConflictError):
    """An account with this email already exists."""

    error_code = "EMAIL_ALREADY_EXISTS"


# --- 422 Unprocessable Entity ------------------------------------------------


class UnprocessableError(HTTPError):
    """Request is well-formed but semantically invalid."""

    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "UNPROCESSABLE_ENTITY"


# --- 429 Too Many Requests ---------------------------------------------------


class RateLimitExceededError(HTTPError):
    """User has exceeded the allowed request rate."""

    status_code = HTTPStatus.TOO_MANY_REQUESTS
    error_code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, retry_after_seconds: int = 60) -> None:
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after_seconds} seconds.",
            details={"retry_after_seconds": retry_after_seconds},
        )
        self.retry_after_seconds = retry_after_seconds


# --- 503 Service Unavailable -------------------------------------------------


class ServiceUnavailableError(HTTPError):
    """Downstream service is unavailable."""

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    error_code = "SERVICE_UNAVAILABLE"


class AllProvidersUnavailableError(ServiceUnavailableError):
    """All LLM providers are currently down or degraded."""

    error_code = "ALL_PROVIDERS_UNAVAILABLE"


class ProviderError(ServiceUnavailableError):
    """A specific LLM provider returned an error."""

    error_code = "PROVIDER_ERROR"

    def __init__(self, provider: str, message: str) -> None:
        super().__init__(
            message=f"Provider '{provider}' returned an error: {message}",
            details={"provider": provider},
        )
        self.provider = provider


# ---------------------------------------------------------------------------
# Infrastructure exceptions (not HTTP-facing directly)
# ---------------------------------------------------------------------------


class DatabaseError(VeloraError):
    """Unexpected database-level error."""


class CacheError(VeloraError):
    """Redis cache operation failed."""


class ConfigurationError(VeloraError):
    """Invalid or missing application configuration."""
