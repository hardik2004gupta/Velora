"""Chat request / response schemas — Phase 2."""

from __future__ import annotations

import uuid
from typing import Annotated, Literal

from pydantic import Field

from app.core.constants import ALL_PROVIDERS, STRATEGY_AUTO
from app.schemas.common import VeloraBaseModel


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


class ChatMessage(VeloraBaseModel):
    """A single message in the conversation history."""

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# Phase 2 — direct provider selection
# ---------------------------------------------------------------------------


class ChatRequest(VeloraBaseModel):
    """Body for POST /chat and POST /chat/stream."""

    messages: list[ChatMessage] = Field(min_length=1)
    provider: str = Field(description="Provider ID: openai | anthropic | gemini")
    model: str | None = Field(default=None, description="Model ID; provider default if omitted")
    max_tokens: Annotated[int, Field(ge=1, le=8192)] = 1024
    temperature: Annotated[float, Field(ge=0.0, le=2.0)] = 0.7
    conversation_id: str | None = None  # client-side session tracking


class ChatResponse(VeloraBaseModel):
    """Non-streaming response for POST /chat."""

    content: str
    provider: str
    model: str
    finish_reason: str


class StreamChunk(VeloraBaseModel):
    """A single SSE event payload for POST /chat/stream."""

    type: Literal["delta", "done", "error"]
    content: str | None = None     # present on type=delta
    provider: str | None = None    # present on type=done
    model: str | None = None       # present on type=done
    finish_reason: str | None = None  # present on type=done
    message: str | None = None     # present on type=error


# ---------------------------------------------------------------------------
# Phase 3+ — routing-aware (kept for forward compatibility)
# ---------------------------------------------------------------------------


class ChatCompletionRequest(VeloraBaseModel):
    """Body for POST /chat/completions (routing-aware, Phase 3+)."""

    messages: list[ChatMessage] = Field(min_length=1)
    routing_strategy: str = Field(default=STRATEGY_AUTO)
    model: str | None = None
    max_tokens: Annotated[int, Field(ge=1, le=8192)] = 1024
    temperature: Annotated[float, Field(ge=0.0, le=2.0)] = 0.7
    stream: bool = True


class RoutingCandidate(VeloraBaseModel):
    provider: str
    model: str
    cost_per_1k: float
    avg_latency_ms: int
    health: str
    quality_score: float
    score: float


class RoutingDecision(VeloraBaseModel):
    strategy: str
    candidates: list[RoutingCandidate]
    selected: str
    reason: str


class TokenUsage(VeloraBaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


class ChatCompletionResponse(VeloraBaseModel):
    """Response for POST /chat/completions (Phase 3+)."""

    request_id: uuid.UUID
    content: str
    routing_decision: RoutingDecision
    usage: TokenUsage
    latency_ms: int
    provider: str
    model: str
    cache_hit: bool
