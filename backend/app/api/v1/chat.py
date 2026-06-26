"""Chat completions endpoints — Phase 4 (routing-aware + request logging)."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.exceptions import ServiceUnavailableError
from app.core.logging import get_logger
from app.database.session import AsyncSessionLocal
from app.dependencies.auth import get_current_user
from app.dependencies.router import get_router_service
from app.models.user import User
from app.providers.registry import get_registry
from app.schemas.chat import ChatRequest, ChatResponse, RoutingCandidate, RoutingDecision
from app.services.request_logger import RequestLoggerService
from app.services.router_service import RoutingResult, RouterService

router = APIRouter()
log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _routing_result_to_schema(result: RoutingResult) -> RoutingDecision:
    return RoutingDecision(
        strategy=result.strategy,
        selected=f"{result.selected_provider_id}/{result.selected_model}",
        reason=result.reason,
        candidates=[
            RoutingCandidate(
                provider=c.provider_id,
                model=c.model_id,
                cost_per_1k=c.cost_per_1k,
                avg_latency_ms=c.latency_ms,
                health=c.health,
                quality_score=c.quality_score,
                score=c.score,
                score_breakdown=c.score_breakdown,
            )
            for c in result.candidates
        ],
    )


def _estimate_tokens(text: str) -> int:
    """4 chars ≈ 1 token — consistent with provider.count_tokens()."""
    return max(1, len(text) // 4)


def _last_user_message(messages: list) -> str:
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content
    return ""


async def _log_request_bg(
    *,
    user_id: uuid.UUID,
    prompt: str,
    response_text: str,
    provider: str,
    model: str,
    routing_strategy: str,
    routing_decision_dict: dict,
    routing_reason: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: int,
    error_message: str | None,
    conversation_id: str | None,
) -> None:
    """Persist a completed request using its own DB session (fire-and-forget)."""
    async with AsyncSessionLocal() as db:
        try:
            svc = RequestLoggerService(db)
            if error_message:
                await svc.log_error(
                    user_id=user_id,
                    prompt=prompt,
                    provider=provider,
                    model=model,
                    routing_strategy=routing_strategy,
                    routing_decision=routing_decision_dict,
                    routing_reason=routing_reason,
                    latency_ms=latency_ms,
                    error_message=error_message,
                    conversation_id=conversation_id,
                )
            else:
                await svc.log_success(
                    user_id=user_id,
                    prompt=prompt,
                    response=response_text,
                    provider=provider,
                    model=model,
                    routing_strategy=routing_strategy,
                    routing_decision=routing_decision_dict,
                    routing_reason=routing_reason,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    latency_ms=latency_ms,
                    conversation_id=conversation_id,
                )
            await db.commit()
        except Exception as exc:
            await db.rollback()
            log.error("request_logging_failed", error=str(exc))


async def _run_stream(
    routing_result: RoutingResult,
    req_body: dict,
    response_collector: list[str],
    error_collector: list[str],
) -> AsyncGenerator[str, None]:
    """Stream tokens from the selected provider, collecting them for logging."""
    registry = get_registry()
    routing_schema = _routing_result_to_schema(routing_result)

    try:
        provider = registry.get(routing_result.selected_provider_id)
    except Exception as exc:
        error_collector.append(str(exc))
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
        return

    normalized = provider.normalize_request(
        messages=req_body["messages"],
        model=routing_result.selected_model,
        max_tokens=req_body.get("max_tokens", 1024),
        temperature=req_body.get("temperature", 0.7),
    )
    normalized["stream"] = True

    try:
        async for token in provider.call(normalized):
            response_collector.append(token)
            yield f"data: {json.dumps({'type': 'delta', 'content': token})}\n\n"

        done_payload = {
            "type": "done",
            "provider": routing_result.selected_provider_id,
            "model": routing_result.selected_model,
            "finish_reason": "stop",
            "routing_decision": routing_schema.model_dump(),
        }
        yield f"data: {json.dumps(done_payload)}\n\n"

    except Exception as exc:
        error_collector.append(str(exc))
        log.error(
            "provider_stream_error",
            provider=routing_result.selected_provider_id,
            error=str(exc),
        )
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/stream", summary="Streaming chat via Server-Sent Events (routing-aware)")
async def chat_stream(
    payload: ChatRequest,
    request: Request,
    user: User = Depends(get_current_user),
    router_svc: RouterService = Depends(get_router_service),
) -> StreamingResponse:
    """
    Route the request, then stream token deltas via SSE.

    SSE event shapes::

        data: {"type": "delta",  "content": "token text"}
        data: {"type": "done",   "provider": "openai", "model": "gpt-4o-mini",
                                  "finish_reason": "stop", "routing_decision": {...}}
        data: {"type": "error",  "message": "reason"}
    """
    routing_result = router_svc.select(
        strategy=payload.routing_strategy,
        manual_provider_id=payload.manual_provider,
        manual_model_id=payload.model,
    )
    log.info(
        "routing_selected",
        strategy=routing_result.strategy,
        provider=routing_result.selected_provider_id,
        model=routing_result.selected_model,
    )

    prompt = _last_user_message(payload.messages)
    prompt_tokens = sum(_estimate_tokens(m.content) for m in payload.messages)
    routing_schema = _routing_result_to_schema(routing_result)
    req_body = {
        "messages": [m.model_dump() for m in payload.messages],
        "max_tokens": payload.max_tokens,
        "temperature": payload.temperature,
    }

    response_collector: list[str] = []
    error_collector: list[str] = []
    start_time = time.monotonic()

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for chunk in _run_stream(
                routing_result, req_body, response_collector, error_collector
            ):
                if await request.is_disconnected():
                    if not error_collector:
                        error_collector.append("Client disconnected")
                    break
                yield chunk
        finally:
            latency_ms = int((time.monotonic() - start_time) * 1_000)
            response_text = "".join(response_collector)
            asyncio.create_task(
                _log_request_bg(
                    user_id=user.id,
                    prompt=prompt,
                    response_text=response_text,
                    provider=routing_result.selected_provider_id,
                    model=routing_result.selected_model,
                    routing_strategy=routing_result.strategy,
                    routing_decision_dict=routing_schema.model_dump(),
                    routing_reason=routing_result.reason,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=_estimate_tokens(response_text),
                    latency_ms=latency_ms,
                    error_message=error_collector[0] if error_collector else None,
                    conversation_id=payload.conversation_id,
                )
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("", response_model=ChatResponse, summary="Non-streaming chat completion (routing-aware)")
async def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    router_svc: RouterService = Depends(get_router_service),
) -> ChatResponse:
    """Route the request, call the selected provider, return the full response."""
    routing_result = router_svc.select(
        strategy=payload.routing_strategy,
        manual_provider_id=payload.manual_provider,
        manual_model_id=payload.model,
    )
    log.info(
        "routing_selected",
        strategy=routing_result.strategy,
        provider=routing_result.selected_provider_id,
        model=routing_result.selected_model,
    )

    registry = get_registry()
    provider = registry.get(routing_result.selected_provider_id)
    messages = [m.model_dump() for m in payload.messages]
    prompt = _last_user_message(payload.messages)
    prompt_tokens = sum(_estimate_tokens(m.content) for m in payload.messages)
    routing_schema = _routing_result_to_schema(routing_result)

    normalized = provider.normalize_request(
        messages=messages,
        model=routing_result.selected_model,
        max_tokens=payload.max_tokens,
        temperature=payload.temperature,
    )
    normalized["stream"] = False

    start_time = time.monotonic()
    parts: list[str] = []
    error_msg: str | None = None

    try:
        async for chunk in provider.call(normalized):
            parts.append(chunk)
    except Exception as exc:
        error_msg = str(exc)

    latency_ms = int((time.monotonic() - start_time) * 1_000)
    response_text = "".join(parts)

    # Fire-and-forget — uses its own session, independent of request lifecycle
    asyncio.create_task(
        _log_request_bg(
            user_id=user.id,
            prompt=prompt,
            response_text=response_text,
            provider=routing_result.selected_provider_id,
            model=routing_result.selected_model,
            routing_strategy=routing_result.strategy,
            routing_decision_dict=routing_schema.model_dump(),
            routing_reason=routing_result.reason,
            prompt_tokens=prompt_tokens,
            completion_tokens=_estimate_tokens(response_text),
            latency_ms=latency_ms,
            error_message=error_msg,
            conversation_id=payload.conversation_id,
        )
    )

    if error_msg:
        log.error(
            "provider_call_error",
            provider=routing_result.selected_provider_id,
            error=error_msg,
        )
        raise ServiceUnavailableError(
            f"Provider '{routing_result.selected_provider_id}' failed: {error_msg}"
        )

    return ChatResponse(
        content=response_text,
        provider=routing_result.selected_provider_id,
        model=routing_result.selected_model,
        finish_reason="stop",
        routing_decision=routing_schema,
    )


@router.post("/completions", summary="Alias — use /chat/stream for streaming")
async def chat_completions() -> dict:
    return {"message": "Use POST /api/v1/chat/stream for streaming or POST /api/v1/chat for non-streaming."}
