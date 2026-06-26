"""Chat completions endpoints — Phase 3 (routing-aware)."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.exceptions import ServiceUnavailableError
from app.core.logging import get_logger
from app.dependencies.auth import get_current_user
from app.dependencies.router import get_router_service
from app.models.user import User
from app.providers.registry import get_registry
from app.schemas.chat import ChatRequest, ChatResponse, RoutingCandidate, RoutingDecision
from app.services.router_service import RoutingResult, RouterService

router = APIRouter()
log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _routing_result_to_schema(result: RoutingResult) -> RoutingDecision:
    """Convert internal RoutingResult dataclass → serialisable RoutingDecision schema."""
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


async def _run_stream(
    routing_result: RoutingResult,
    req_body: dict,
) -> AsyncGenerator[str, None]:
    """Stream tokens from the selected provider, emitting SSE lines."""
    registry = get_registry()
    routing_schema = _routing_result_to_schema(routing_result)

    try:
        provider = registry.get(routing_result.selected_provider_id)
    except Exception as exc:
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
    _user: User = Depends(get_current_user),
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

    req_body = {
        "messages": [m.model_dump() for m in payload.messages],
        "max_tokens": payload.max_tokens,
        "temperature": payload.temperature,
    }

    async def event_generator() -> AsyncGenerator[str, None]:
        async for chunk in _run_stream(routing_result, req_body):
            if await request.is_disconnected():
                break
            yield chunk

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
    _user: User = Depends(get_current_user),
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

    normalized = provider.normalize_request(
        messages=messages,
        model=routing_result.selected_model,
        max_tokens=payload.max_tokens,
        temperature=payload.temperature,
    )
    normalized["stream"] = False

    parts: list[str] = []
    try:
        async for chunk in provider.call(normalized):
            parts.append(chunk)
    except Exception as exc:
        log.error(
            "provider_call_error",
            provider=routing_result.selected_provider_id,
            error=str(exc),
        )
        raise ServiceUnavailableError(
            f"Provider '{routing_result.selected_provider_id}' failed: {exc}"
        ) from exc

    return ChatResponse(
        content="".join(parts),
        provider=routing_result.selected_provider_id,
        model=routing_result.selected_model,
        finish_reason="stop",
        routing_decision=_routing_result_to_schema(routing_result),
    )


@router.post("/completions", summary="Routing-aware completions with caching (Phase 4+)")
async def chat_completions() -> dict:
    return {"message": "Request persistence and caching are implemented in Phase 4."}
