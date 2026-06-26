"""
Standard API response builders.

Every error response uses the same envelope shape::

    {
        "error": {
            "code": "NOT_FOUND",
            "message": "User not found.",
            "details": {}
        }
    }

This consistency makes error handling predictable on the frontend.
"""

from __future__ import annotations

from typing import Any

from fastapi.responses import ORJSONResponse

from app.core.exceptions import HTTPError


def error_response(
    exc: HTTPError,
    *,
    headers: dict[str, str] | None = None,
) -> ORJSONResponse:
    """Build a standard error response from an ``HTTPError`` instance."""
    content = {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        }
    }
    return ORJSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=headers,
    )


def validation_error_response(errors: list[dict[str, Any]]) -> ORJSONResponse:
    """Build a standard 422 response for Pydantic validation failures."""
    return ORJSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": {"errors": errors},
            }
        },
    )
