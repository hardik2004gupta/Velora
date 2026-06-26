"""Chat request / response schemas — Phase 3."""

from __future__ import annotations

import uuid
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.core.constants import ALL_STRATEGIES, STRATEGY_AUTO
from app.schemas.common import VeloraBaseModel


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


class ChatMessage(VeloraBaseModel):
    """A single message in the conversation history."""

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# Routing Decision (returned with every response)
# ---------------------------------------------------------------------------


class RoutingCandidate(VeloraBaseModel):
    """One (provider, model) pair evaluated by the router."""

    provider: str
    model: str
    cost_per_1k: float
    avg_latency_ms: int
    health: str
    quality_score: float
    score: float
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class RoutingDecision(VeloraBaseModel):
    """Complete routing report attached to every chat response."""

    strategy: str
    candidates: list[RoutingCandidate]
    selected: str   # "provider/model"
    reason: str


# ---------------------------------------------------------------------------
# Phase 3 — routing-aware request
# ---------------------------------------------------------------------------


class ChatRequest(VeloraBaseModel):
    """Body for POST /chat and POST /chat/stream."""

    messages: list[ChatMessage] = Field(min_length=1)

    # Routing strategy (auto | cheapest | fastest | quality | manual)
    routing_strategy: str = Field(default=STRATEGY_AUTO)

    # Only used when routing_strategy == "manual"
    manual_provider: str | None = Field(default=None)

    model: str | None = Field(default=None, description="Explicit model override (manual mode)")
    max_tokens: Annotated[int, Field(ge=1, le=8192)] = 1024
    temperature: Annotated[float, Field(ge=0.0, le=2.0)] = 0.7
    conversation_id: str | None = None

    @model_validator(mode="after")
    def validate_manual_provider(self) -> "ChatRequest":
        if self.routing_strategy == "manual" and not self.manual_provider:
            raise ValueError("manual_provider is required when routing_strategy is 'manual'.")
        return self


class ChatResponse(VeloraBaseModel):
    """Non-streaming response for POST /chat."""

    content: str
    provider: str
    model: str
    finish_reason: str
    routing_decision: RoutingDecision
    cache_hit: bool = False
    fallback_provider: str | None = None


class StreamChunk(VeloraBaseModel):
    """A single SSE event payload for POST /chat/stream."""

    type: Literal["delta", "done", "error"]
    content: str | None = None              # type=delta
    provider: str | None = None             # type=done
    model: str | None = None                # type=done
    finish_reason: str | None = None        # type=done
    routing_decision: RoutingDecision | None = None  # type=done
    message: str | None = None              # type=error
    cache_hit: bool | None = None           # type=done
    fallback_provider: str | None = None    # type=done — set when fallback was used


# ---------------------------------------------------------------------------
# Phase 4+ — placeholder (kept for forward compatibility)
# ---------------------------------------------------------------------------


class TokenUsage(VeloraBaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


class ChatCompletionResponse(VeloraBaseModel):
    """Response for POST /chat/completions (Phase 4+ with caching and cost tracking)."""

    request_id: uuid.UUID
    content: str
    routing_decision: RoutingDecision
    usage: TokenUsage
    latency_ms: int
    provider: str
    model: str
    cache_hit: bool
