"""
Security utilities — JWT creation/validation, password hashing, API key helpers.

JWT tokens:
    Access token  — short-lived (15 min default), type="access"
    Refresh token — long-lived (30 day default), type="refresh", jti=session_id

API keys:
    Format:  ``vk-{43 url-safe chars}``  (32 random bytes base64url-encoded)
    Storage: bcrypt(key) — never plaintext
    Lookup:  key_prefix (first 8 chars) → bcrypt.verify(incoming, stored)

Passwords:
    bcrypt, cost factor 12
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.core.constants import API_KEY_LENGTH, API_KEY_PREFIX
from app.core.exceptions import ExpiredTokenError, InvalidTokenError

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# Token type literals injected into the JWT payload
_TOKEN_TYPE_ACCESS = "access"
_TOKEN_TYPE_REFRESH = "refresh"


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
# JWT — access tokens
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
        subject: The ``sub`` claim — the user's UUID string.
        expires_delta: Custom expiry.  Defaults to ``JWT_ACCESS_TOKEN_EXPIRE_MINUTES``.
        extra_claims: Additional claims merged into the payload.

    Returns:
        A compact JWT string.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    delta = expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": _TOKEN_TYPE_ACCESS,
        "iat": now,
        "exp": now + delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str, session_id: str) -> str:
    """
    Create a signed JWT refresh token.

    The ``jti`` claim ties this token to a ``Session`` row so that logout
    can be enforced by deleting the session from the database.

    Args:
        subject: The user's UUID string.
        session_id: The ``Session.id`` UUID string.

    Returns:
        A compact JWT string.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    delta = timedelta(days=settings.jwt_refresh_token_expire_days)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": _TOKEN_TYPE_REFRESH,
        "jti": session_id,
        "iat": now,
        "exp": now + delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate any JWT (access or refresh).

    Raises:
        ExpiredTokenError: Token signature is valid but has expired.
        InvalidTokenError: Token is malformed or signature is wrong.

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
        raise ExpiredTokenError("Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError(f"Token is invalid: {exc}") from exc


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT, asserting it is an access token.

    Raises:
        InvalidTokenError: If the ``type`` claim is not ``"access"``.
    """
    payload = decode_token(token)
    if payload.get("type") != _TOKEN_TYPE_ACCESS:
        raise InvalidTokenError("Token is not an access token.")
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT, asserting it is a refresh token.

    Raises:
        InvalidTokenError: If the ``type`` claim is not ``"refresh"``.
    """
    payload = decode_token(token)
    if payload.get("type") != _TOKEN_TYPE_REFRESH:
        raise InvalidTokenError("Token is not a refresh token.")
    return payload


def extract_subject(token: str) -> str:
    """Decode an access token and return its ``sub`` claim."""
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
    Generate a cryptographically secure Velora API key.

    Format: ``vk-{43 URL-safe chars}``  (32 random bytes → base64url → ~43 chars)
    Returns the full key — it is only available at creation time.
    """
    random_part = secrets.token_urlsafe(API_KEY_LENGTH)
    return f"{API_KEY_PREFIX}{random_part}"


def get_api_key_prefix(key: str) -> str:
    """Return the first 8 characters of *key* for display in the UI."""
    return key[:8]


def hash_api_key(key: str) -> str:
    """Return a bcrypt hash of the full API key for storage."""
    return _pwd_context.hash(key)  # type: ignore[no-any-return]


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Constant-time verification of an API key against its stored hash.

    Uses passlib's bcrypt.verify which is inherently timing-safe.
    """
    return _pwd_context.verify(plain_key, hashed_key)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Refresh token helpers — for session storage
# ---------------------------------------------------------------------------


def hash_refresh_token(token: str) -> str:
    """
    Return a SHA-256 hex digest of *token* for session table storage.

    This is used for fast O(1) session lookup — we can't bcrypt the refresh
    token because we need to find the session record by hash, not by prefix.
    SHA-256 is safe here because the token has 256 bits of entropy.
    """
    return hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------


def slugify(name: str) -> str:
    """
    Convert *name* to a URL-safe slug.

    Converts to lowercase, replaces spaces/special chars with hyphens,
    and strips leading/trailing hyphens.

    Example::
        slugify("My Cool Org!")  → "my-cool-org"
    """
    import re
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")
