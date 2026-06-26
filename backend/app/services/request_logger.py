"""Request logger — persists every inference call to PostgreSQL."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import REQUEST_STATUS_ERROR, REQUEST_STATUS_SUCCESS
from app.core.logging import get_logger
from app.models.request import Request
from app.services.cost_service import CostService

log = get_logger(__name__)

_cost_svc = CostService()


def _generate_request_id() -> str:
    """Generate a human-readable unique request ID like req_a1b2c3d4e5f6g7h8."""
    return "req_" + secrets.token_hex(8)


def _hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()


class RequestLoggerService:
    """Persists request metadata, tokens, cost, and routing to the requests table."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def log_success(
        self,
        *,
        user_id: uuid.UUID,
        prompt: str,
        response: str,
        provider: str,
        model: str,
        routing_strategy: str,
        routing_decision: dict,
        routing_reason: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        conversation_id: str | None = None,
    ) -> Request:
        cost = _cost_svc.calculate(provider, model, prompt_tokens, completion_tokens)
        total_tokens = prompt_tokens + completion_tokens

        record = Request(
            request_id=_generate_request_id(),
            user_id=user_id,
            conversation_id=conversation_id,
            prompt=prompt,
            response=response,
            provider=provider,
            model=model,
            routing_strategy=routing_strategy,
            routing_decision=routing_decision,
            routing_reason=routing_reason,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost.total_cost,
            latency_ms=latency_ms,
            cache_hit=False,
            status=REQUEST_STATUS_SUCCESS,
            error_message=None,
            prompt_hash=_hash_prompt(prompt),
            created_at=datetime.now(UTC),
        )
        self._db.add(record)
        await self._db.flush()
        log.info(
            "request_logged",
            request_id=record.request_id,
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            total_tokens=total_tokens,
            cost_usd=float(cost.total_cost),
        )
        return record

    async def log_error(
        self,
        *,
        user_id: uuid.UUID,
        prompt: str,
        provider: str,
        model: str,
        routing_strategy: str,
        routing_decision: dict,
        routing_reason: str,
        latency_ms: int,
        error_message: str,
        conversation_id: str | None = None,
    ) -> Request:
        record = Request(
            request_id=_generate_request_id(),
            user_id=user_id,
            conversation_id=conversation_id,
            prompt=prompt,
            response=None,
            provider=provider,
            model=model,
            routing_strategy=routing_strategy,
            routing_decision=routing_decision,
            routing_reason=routing_reason,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            cost_usd=0.0,
            latency_ms=latency_ms,
            cache_hit=False,
            status=REQUEST_STATUS_ERROR,
            error_message=error_message,
            prompt_hash=_hash_prompt(prompt),
            created_at=datetime.now(UTC),
        )
        self._db.add(record)
        await self._db.flush()
        log.info(
            "error_request_logged",
            request_id=record.request_id,
            provider=provider,
            model=model,
            error=error_message,
        )
        return record
