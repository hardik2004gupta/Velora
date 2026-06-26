"""Request history schemas — Phase 4."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import field_validator

from app.schemas.chat import RoutingDecision
from app.schemas.common import VeloraBaseModel

_PROMPT_PREVIEW_LENGTH = 200


class RequestSummary(VeloraBaseModel):
    """Compact record for list views — prompt truncated for performance."""

    id: uuid.UUID
    request_id: str | None
    conversation_id: str | None
    provider: str
    model: str
    routing_strategy: str
    prompt: str | None
    total_tokens: int
    cost_usd: float
    latency_ms: int | None
    cache_hit: bool
    status: str
    created_at: datetime

    @field_validator("prompt", mode="before")
    @classmethod
    def truncate_prompt(cls, v: str | None) -> str | None:
        if v and len(v) > _PROMPT_PREVIEW_LENGTH:
            return v[:_PROMPT_PREVIEW_LENGTH] + "…"
        return v


class RequestDetail(VeloraBaseModel):
    """Full record including prompt, response, and routing decision."""

    id: uuid.UUID
    request_id: str | None
    conversation_id: str | None
    provider: str
    model: str
    routing_strategy: str
    routing_reason: str | None
    prompt: str | None
    response: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: int | None
    cache_hit: bool
    status: str
    error_message: str | None
    routing_decision: RoutingDecision | None
    created_at: datetime


class RequestListResponse(VeloraBaseModel):
    """Paginated response for GET /requests."""

    items: list[RequestSummary]
    total: int
    page: int
    limit: int
    has_next: bool
