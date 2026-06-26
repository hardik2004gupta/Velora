"""Request history schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.schemas.chat import RoutingDecision
from app.schemas.common import VeloraBaseModel


class RequestSummary(VeloraBaseModel):
    """Compact request record for list views."""

    id: uuid.UUID
    provider: str
    model: str
    routing_strategy: str
    total_tokens: int
    cost_usd: float
    latency_ms: int
    cache_hit: bool
    status: str
    created_at: datetime


class RequestDetail(RequestSummary):
    """Full request record including routing decision."""

    prompt_tokens: int
    completion_tokens: int
    error_message: str | None
    routing_decision: RoutingDecision


class RequestListResponse(VeloraBaseModel):
    """Response for GET /requests."""

    items: list[RequestSummary]
    total: int
    page: int
    limit: int
