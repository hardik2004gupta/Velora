"""Unit tests for cache key builders."""

from __future__ import annotations

from app.cache.keys import build_prompt_hash, prompt_cache_key, rate_limit_key


class TestPromptHash:
    def test_same_inputs_same_hash(self) -> None:
        h1 = build_prompt_hash("hello world", "gpt-4o-mini", 0.7, 1024)
        h2 = build_prompt_hash("hello world", "gpt-4o-mini", 0.7, 1024)
        assert h1 == h2

    def test_whitespace_normalised(self) -> None:
        h1 = build_prompt_hash("hello   world", "gpt-4o-mini", 0.7, 1024)
        h2 = build_prompt_hash("hello world", "gpt-4o-mini", 0.7, 1024)
        assert h1 == h2

    def test_different_model_different_hash(self) -> None:
        h1 = build_prompt_hash("hello", "gpt-4o-mini", 0.7, 1024)
        h2 = build_prompt_hash("hello", "gpt-4o", 0.7, 1024)
        assert h1 != h2

    def test_different_temperature_different_hash(self) -> None:
        h1 = build_prompt_hash("hello", "gpt-4o-mini", 0.7, 1024)
        h2 = build_prompt_hash("hello", "gpt-4o-mini", 0.5, 1024)
        assert h1 != h2

    def test_hash_is_64_hex_chars(self) -> None:
        h = build_prompt_hash("test", "model", 0.7, 100)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestCacheKey:
    def test_prompt_cache_key_format(self) -> None:
        key = prompt_cache_key("abc123")
        assert key == "cache:abc123"

    def test_rate_limit_key_contains_user_id(self) -> None:
        key = rate_limit_key("user-uuid-123")
        assert "user-uuid-123" in key
        assert key.startswith("rate:")
