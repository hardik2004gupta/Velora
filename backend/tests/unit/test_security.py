"""Unit tests for security utilities."""

from __future__ import annotations

import pytest

from app.core.exceptions import ExpiredTokenError, InvalidTokenError
from app.core.security import (
    create_access_token,
    decode_access_token,
    extract_subject,
    generate_api_key,
    get_api_key_prefix,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self) -> None:
        plain = "super-secret-password"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed)

    def test_wrong_password_fails(self) -> None:
        hashed = hash_password("correct-password")
        assert not verify_password("wrong-password", hashed)

    def test_hash_is_not_plain_text(self) -> None:
        plain = "my-password"
        assert hash_password(plain) != plain

    def test_same_plain_produces_different_hashes(self) -> None:
        plain = "same-password"
        assert hash_password(plain) != hash_password(plain)


class TestJWT:
    def test_create_and_decode(self) -> None:
        token = create_access_token(subject="user-123")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-123"

    def test_extract_subject(self) -> None:
        token = create_access_token(subject="user-abc")
        assert extract_subject(token) == "user-abc"

    def test_invalid_token_raises(self) -> None:
        with pytest.raises(InvalidTokenError):
            decode_access_token("not.a.valid.token")

    def test_tampered_token_raises(self) -> None:
        token = create_access_token(subject="user-123")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(InvalidTokenError):
            decode_access_token(tampered)


class TestAPIKeyHelpers:
    def test_key_starts_with_prefix(self) -> None:
        key = generate_api_key()
        assert key.startswith("vk-")

    def test_key_is_unique(self) -> None:
        assert generate_api_key() != generate_api_key()

    def test_prefix_returns_first_8_chars(self) -> None:
        key = "vk-abc123xyz"
        assert get_api_key_prefix(key) == "vk-abc12"
