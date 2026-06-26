"""
Authentication service.

Coordinates registration, login, token refresh, and logout.
All credential logic lives here — routes only call this service.

Audit events emitted:
    user_registered, user_login, user_login_failed,
    user_logout, refresh_token_rotated
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    EmailAlreadyExistsError,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.session import Session
from app.models.user import User
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest, TokenPairResponse

log = get_logger(__name__)


class AuthService:
    """
    Stateless authentication service.

    Depends on ``UserRepository`` and ``SessionRepository`` which are injected
    per-request via the DI system.
    """

    def __init__(
        self,
        db: AsyncSession,
        user_repo: UserRepository | None = None,
        session_repo: SessionRepository | None = None,
    ) -> None:
        self._db = db
        self._user_repo = user_repo or UserRepository(db)
        self._session_repo = session_repo or SessionRepository(db)

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------

    async def register(
        self,
        payload: RegisterRequest,
        *,
        request_id: str = "",
    ) -> tuple[User, TokenPairResponse]:
        """
        Create a new user account and issue tokens.

        Raises:
            EmailAlreadyExistsError: If the email is already registered.
        """
        if await self._user_repo.exists_by_email(payload.email):
            log.warning("register_email_conflict", email=payload.email, request_id=request_id)
            raise EmailAlreadyExistsError(
                f"An account with email {payload.email!r} already exists."
            )

        user = await self._user_repo.create(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            is_verified=False,
        )
        tokens = await self._issue_tokens(user, request_id=request_id)

        log.info(
            "user_registered",
            user_id=str(user.id),
            email=user.email,
            request_id=request_id,
        )
        return user, tokens

    # -------------------------------------------------------------------------
    # Login
    # -------------------------------------------------------------------------

    async def login(
        self,
        email: str,
        password: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str = "",
    ) -> tuple[User, TokenPairResponse]:
        """
        Validate credentials and issue a token pair.

        Raises:
            AuthenticationError: On any credential failure (message is generic
                to prevent user-enumeration attacks).
        """
        user = await self._user_repo.get_by_email(email)
        _generic_error = "Invalid email or password."

        if user is None:
            # Perform a dummy verify to prevent timing-based enumeration
            _dummy_hash = "$2b$12$DUMMY_HASH_TO_PREVENT_TIMING_ATTACK_PADDING"
            verify_password(password, _dummy_hash)
            log.warning(
                "login_failed_unknown_email",
                email=email,
                ip=ip_address,
                request_id=request_id,
            )
            raise AuthenticationError(_generic_error)

        if not verify_password(password, user.hashed_password):
            log.warning(
                "login_failed_wrong_password",
                user_id=str(user.id),
                email=email,
                ip=ip_address,
                request_id=request_id,
            )
            raise AuthenticationError(_generic_error)

        if not user.is_active:
            log.warning(
                "login_failed_inactive",
                user_id=str(user.id),
                request_id=request_id,
            )
            raise AuthenticationError("Account is disabled. Contact support.")

        tokens = await self._issue_tokens(
            user,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )
        log.info(
            "user_login",
            user_id=str(user.id),
            email=user.email,
            ip=ip_address,
            request_id=request_id,
        )
        return user, tokens

    # -------------------------------------------------------------------------
    # Token refresh
    # -------------------------------------------------------------------------

    async def refresh(
        self,
        refresh_token: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str = "",
    ) -> TokenPairResponse:
        """
        Validate a refresh token, rotate it, and issue a new pair.

        Implements refresh token rotation: the old session is deleted and a
        new one is created atomically, preventing replay attacks.

        Raises:
            AuthenticationError: If the token is invalid, expired, or revoked.
        """
        token_hash = hash_refresh_token(refresh_token)
        session = await self._session_repo.get_by_token_hash(token_hash)
        if session is None:
            log.warning(
                "refresh_token_not_found",
                request_id=request_id,
                ip=ip_address,
            )
            raise AuthenticationError("Refresh token has been revoked or expired.")

        user = await self._user_repo.get_active_by_id(session.user_id)
        if user is None:
            raise AuthenticationError("User account no longer exists or is disabled.")

        # Rotate: delete old session, issue new pair
        await self._session_repo.delete(session)
        tokens = await self._issue_tokens(
            user,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )
        log.info(
            "refresh_token_rotated",
            user_id=str(user.id),
            request_id=request_id,
        )
        return tokens

    # -------------------------------------------------------------------------
    # Logout
    # -------------------------------------------------------------------------

    async def logout(
        self,
        refresh_token: str,
        *,
        request_id: str = "",
        user_id: str = "",
    ) -> None:
        """
        Invalidate the session associated with *refresh_token*.

        This is a best-effort operation: if the session no longer exists
        (already expired or deleted), the logout is still considered successful.
        """
        token_hash = hash_refresh_token(refresh_token)
        deleted = await self._session_repo.delete_by_token_hash(token_hash)
        log.info(
            "user_logout",
            user_id=user_id,
            session_deleted=deleted,
            request_id=request_id,
        )

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    async def _issue_tokens(
        self,
        user: User,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str = "",
    ) -> TokenPairResponse:
        """Create a session record and return a fresh access + refresh pair."""
        import secrets as _secrets
        settings = get_settings()
        now = datetime.now(UTC)

        # Generate an opaque refresh token string (not a JWT — stored as hash)
        raw_refresh_token = _secrets.token_urlsafe(64)
        token_hash = hash_refresh_token(raw_refresh_token)
        expires_at = now + timedelta(days=settings.jwt_refresh_token_expire_days)

        session = await self._session_repo.create(
            user_id=user.id,
            refresh_token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        access_token = create_access_token(subject=str(user.id))

        return TokenPairResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )
