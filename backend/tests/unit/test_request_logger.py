"""Unit tests for RequestLoggerService helpers — no DB required."""

from __future__ import annotations

import re

import pytest

from app.services.request_logger import _generate_request_id, _hash_prompt


class TestGenerateRequestId:
    def test_starts_with_req(self) -> None:
        rid = _generate_request_id()
        assert rid.startswith("req_")

    def test_length(self) -> None:
        rid = _generate_request_id()
        # "req_" (4) + 16 hex chars = 20
        assert len(rid) == 20

    def test_hex_suffix(self) -> None:
        rid = _generate_request_id()
        suffix = rid[4:]
        assert re.fullmatch(r"[0-9a-f]{16}", suffix), f"Not hex: {suffix!r}"

    def test_unique(self) -> None:
        ids = {_generate_request_id() for _ in range(100)}
        assert len(ids) == 100, "Collision detected in 100 IDs"


class TestHashPrompt:
    def test_returns_64_char_hex(self) -> None:
        h = _hash_prompt("hello world")
        assert len(h) == 64
        assert re.fullmatch(r"[0-9a-f]{64}", h)

    def test_deterministic(self) -> None:
        assert _hash_prompt("same input") == _hash_prompt("same input")

    def test_different_inputs_produce_different_hashes(self) -> None:
        assert _hash_prompt("hello") != _hash_prompt("world")

    def test_empty_string(self) -> None:
        h = _hash_prompt("")
        assert len(h) == 64
