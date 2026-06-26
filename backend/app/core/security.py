"""
Security utilities — JWT creation/validation and password hashing.

Passwords are hashed with bcrypt (cost factor 12).
JWTs are signed with HS256.

Usage::

    from app.core.security import create_access_token, verify_password

    token = create_access_token(subject="user-uuid")
    ok = verify_password("plain", hashed)
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.core.constants import API_KEY_LENGTH, API_KEY_PREFIX
from app.core.exceptions import ExpiredTokenError, InvalidTokenError

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------


def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of *plain_password*."""
    return _pwd_context.hash(plain_password)  # type: ignore[no-any-return]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches the stored *hashed_password*."""
    return _pwd_context.verify(plain_password, hashed_password)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_access_token(
    subject: str,
    *,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: The ``sub`` claim — typically the user's UUID string.
        expires_delta: Custom expiry.  Defaults to ``JWT_ACCESS_TOKEN_EXPIRE_MINUTES``.
        extra_claims: Any additional claims to include in the payload.

    Returns:
        A compact JWT string.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    delta = expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + delta,
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Raises:
        ExpiredTokenError: Token has passed its expiry time.
        InvalidTokenError: Token is malformed or signature verification failed.

    Returns:
        The decoded payload dictionary.
    """
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenError("Access token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError(f"Access token is invalid: {exc}") from exc


def extract_subject(token: str) -> str:
    """
    Decode a JWT and return the ``sub`` claim.

    Raises:
        InvalidTokenError: If ``sub`` is absent from the payload.
    """
    payload = decode_access_token(token)
    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        raise InvalidTokenError("Token is missing required 'sub' claim.")
    return sub


# ---------------------------------------------------------------------------
# API key helpers
# ---------------------------------------------------------------------------


def generate_api_key() -> str:
    """
    Generate a new Velora API key.

    Format: ``vk-<32 URL-safe random bytes>``
    The full key is returned exactly once — only a hash + prefix are stored.
    """
    random_part = secrets.token_urlsafe(API_KEY_LENGTH)
    return f"{API_KEY_PREFIX}{random_part}"


def get_api_key_prefix(key: str) -> str:
    """Return the first 8 characters of *key* for display in the UI."""
    return key[:8]


def hash_api_key(key: str) -> str:
    """Return a bcrypt hash of the full API key for storage."""
    return _pwd_context.hash(key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Return True if *plain_key* matches the stored *hashed_key*."""
    return _pwd_context.verify(plain_key, hashed_key)
