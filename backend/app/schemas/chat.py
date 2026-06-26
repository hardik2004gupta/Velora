"""Chat request / response schemas."""

from __future__ import annotations

import uuid
from typing import Annotated, Literal

from pydantic import Field

from app.core.constants import ALL_STRATEGIES, STRATEGY_AUTO
from app.schemas.common import VeloraBaseModel


class ChatMessage(VeloraBaseModel):
    """A single message in the conversation history."""

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatCompletionRequest(VeloraBaseModel):
    """Body for POST /chat/completions."""

    messages: list[ChatMessage] = Field(min_length=1)
    routing_strategy: str = Field(default=STRATEGY_AUTO)
    model: str | None = None
    max_tokens: Annotated[int, Field(ge=1, le=8192)] = 1024
    temperature: Annotated[float, Field(ge=0.0, le=2.0)] = 0.7
    stream: bool = True


class RoutingCandidate(VeloraBaseModel):
    """A single candidate evaluated by the router."""

    provider: str
    model: str
    cost_per_1k: float
    avg_latency_ms: int
    health: str
    quality_score: float
    score: float


class RoutingDecision(VeloraBaseModel):
    """Full routing decision object attached to every response."""

    strategy: str
    candidates: list[RoutingCandidate]
    selected: str
    reason: str


class TokenUsage(VeloraBaseModel):
    """Token consumption breakdown."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


class ChatCompletionResponse(VeloraBaseModel):
    """Non-streaming response for POST /chat/completions."""

    request_id: uuid.UUID
    content: str
    routing_decision: RoutingDecision
    usage: TokenUsage
    latency_ms: int
    provider: str
    model: str
    cache_hit: bool
