"""Unit tests for AuthService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from datetime import UTC, datetime, timedelta

import pytest

from app.core.exceptions import AuthenticationError, EmailAlreadyExistsError
from app.schemas.auth import RegisterRequest, TokenPairResponse


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "00000000-0000-0000-0000-000000000001"
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.is_active = True
    user.hashed_password = "$2b$12$fakehash"
    return user


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_user_repo(mock_user):
    repo = AsyncMock()
    repo.exists_by_email.return_value = False
    repo.get_by_email.return_value = mock_user
    repo.get_active_by_id.return_value = mock_user
    repo.create.return_value = mock_user
    return repo


@pytest.fixture
def mock_session_repo():
    repo = AsyncMock()
    mock_session = MagicMock()
    mock_session.user_id = "00000000-0000-0000-0000-000000000001"
    repo.get_by_token_hash.return_value = mock_session
    repo.create.return_value = mock_session
    repo.delete_by_token_hash.return_value = True
    return repo


class TestRegister:
    @pytest.mark.anyio
    async def test_register_success(self, mock_db, mock_user_repo, mock_session_repo, mock_user):
        from app.services.auth_service import AuthService

        service = AuthService(mock_db, user_repo=mock_user_repo, session_repo=mock_session_repo)
        payload = RegisterRequest(email="new@example.com", password="password123", full_name="New User")

        with patch("app.services.auth_service.hash_password", return_value="hashed"):
            user, tokens = await service.register(payload)

        mock_user_repo.exists_by_email.assert_called_once_with("new@example.com")
        mock_user_repo.create.assert_called_once()
        assert isinstance(tokens, TokenPairResponse)
        assert tokens.access_token != ""
        assert tokens.refresh_token != ""

    @pytest.mark.anyio
    async def test_register_duplicate_email(self, mock_db, mock_user_repo, mock_session_repo):
        from app.services.auth_service import AuthService

        mock_user_repo.exists_by_email.return_value = True
        service = AuthService(mock_db, user_repo=mock_user_repo, session_repo=mock_session_repo)
        payload = RegisterRequest(email="existing@example.com", password="password123", full_name="User")

        with pytest.raises(EmailAlreadyExistsError):
            await service.register(payload)


class TestLogin:
    @pytest.mark.anyio
    async def test_login_success(self, mock_db, mock_user_repo, mock_session_repo, mock_user):
        from app.services.auth_service import AuthService

        service = AuthService(mock_db, user_repo=mock_user_repo, session_repo=mock_session_repo)

        with patch("app.services.auth_service.verify_password", return_value=True):
            user, tokens = await service.login("test@example.com", "password123")

        assert user is mock_user
        assert isinstance(tokens, TokenPairResponse)

    @pytest.mark.anyio
    async def test_login_unknown_email(self, mock_db, mock_user_repo, mock_session_repo):
        from app.services.auth_service import AuthService

        mock_user_repo.get_by_email.return_value = None
        service = AuthService(mock_db, user_repo=mock_user_repo, session_repo=mock_session_repo)

        with patch("app.services.auth_service.verify_password", return_value=False):
            with pytest.raises(AuthenticationError):
                await service.login("nobody@example.com", "wrong")

    @pytest.mark.anyio
    async def test_login_wrong_password(self, mock_db, mock_user_repo, mock_session_repo):
        from app.services.auth_service import AuthService

        service = AuthService(mock_db, user_repo=mock_user_repo, session_repo=mock_session_repo)

        with patch("app.services.auth_service.verify_password", return_value=False):
            with pytest.raises(AuthenticationError):
                await service.login("test@example.com", "wrongpassword")

    @pytest.mark.anyio
    async def test_login_inactive_user(self, mock_db, mock_user_repo, mock_session_repo, mock_user):
        from app.services.auth_service import AuthService

        mock_user.is_active = False
        service = AuthService(mock_db, user_repo=mock_user_repo, session_repo=mock_session_repo)

        with patch("app.services.auth_service.verify_password", return_value=True):
            with pytest.raises(AuthenticationError, match="disabled"):
                await service.login("test@example.com", "password123")


class TestRefresh:
    @pytest.mark.anyio
    async def test_refresh_success(self, mock_db, mock_user_repo, mock_session_repo):
        from app.services.auth_service import AuthService

        service = AuthService(mock_db, user_repo=mock_user_repo, session_repo=mock_session_repo)

        with patch("app.services.auth_service.hash_refresh_token", return_value="fakehash"):
            tokens = await service.refresh("some-opaque-token")

        assert isinstance(tokens, TokenPairResponse)
        mock_session_repo.delete.assert_called_once()

    @pytest.mark.anyio
    async def test_refresh_invalid_token(self, mock_db, mock_user_repo, mock_session_repo):
        from app.services.auth_service import AuthService

        mock_session_repo.get_by_token_hash.return_value = None
        service = AuthService(mock_db, user_repo=mock_user_repo, session_repo=mock_session_repo)

        with pytest.raises(AuthenticationError):
            await service.refresh("revoked-token")


class TestLogout:
    @pytest.mark.anyio
    async def test_logout_deletes_session(self, mock_db, mock_user_repo, mock_session_repo):
        from app.services.auth_service import AuthService

        service = AuthService(mock_db, user_repo=mock_user_repo, session_repo=mock_session_repo)
        await service.logout("some-token", user_id="user-123")
        mock_session_repo.delete_by_token_hash.assert_called_once()

    @pytest.mark.anyio
    async def test_logout_already_expired_is_ok(self, mock_db, mock_user_repo, mock_session_repo):
        from app.services.auth_service import AuthService

        mock_session_repo.delete_by_token_hash.return_value = False
        service = AuthService(mock_db, user_repo=mock_user_repo, session_repo=mock_session_repo)
        # Should not raise even if session not found
        await service.logout("expired-token")
