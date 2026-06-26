"""Chat completions endpoints — Phase 2."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.exceptions import ServiceUnavailableError
from app.core.logging import get_logger
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.providers.registry import get_registry
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _run_stream(provider_id: str, req_body: dict) -> AsyncGenerator[str, None]:
    """Call the provider in streaming mode and yield formatted SSE lines."""
    registry = get_registry()
    try:
        provider = registry.get(provider_id)
    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
        return

    model = req_body.get("model") or provider.get_available_models()[0].model_id
    normalized = provider.normalize_request(
        messages=req_body["messages"],
        model=model,
        max_tokens=req_body.get("max_tokens", 1024),
        temperature=req_body.get("temperature", 0.7),
    )
    normalized["stream"] = True

    try:
        async for token in provider.call(normalized):
            yield f"data: {json.dumps({'type': 'delta', 'content': token})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'provider': provider_id, 'model': model, 'finish_reason': 'stop'})}\n\n"
    except Exception as exc:
        log.error("provider_stream_error", provider=provider_id, error=str(exc))
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/stream", summary="Streaming chat via Server-Sent Events")
async def chat_stream(
    payload: ChatRequest,
    request: Request,
    _user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Stream token deltas for a chat request.

    Each SSE event has the shape::

        data: {"type": "delta", "content": "token"}
        data: {"type": "done", "provider": "openai", "model": "gpt-4o-mini", "finish_reason": "stop"}
        data: {"type": "error", "message": "reason"}
    """
    req_body = {
        "messages": [m.model_dump() for m in payload.messages],
        "model": payload.model,
        "max_tokens": payload.max_tokens,
        "temperature": payload.temperature,
    }

    async def event_generator() -> AsyncGenerator[str, None]:
        async for chunk in _run_stream(payload.provider, req_body):
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


@router.post("", response_model=ChatResponse, summary="Non-streaming chat completion")
async def chat(
    payload: ChatRequest,
    _user: User = Depends(get_current_user),
) -> ChatResponse:
    """Complete a chat request and return the full response at once."""
    registry = get_registry()
    provider = registry.get(payload.provider)
    model = payload.model or provider.get_available_models()[0].model_id
    messages = [m.model_dump() for m in payload.messages]

    normalized = provider.normalize_request(
        messages=messages,
        model=model,
        max_tokens=payload.max_tokens,
        temperature=payload.temperature,
    )
    normalized["stream"] = False

    parts: list[str] = []
    try:
        async for chunk in provider.call(normalized):
            parts.append(chunk)
    except Exception as exc:
        log.error("provider_call_error", provider=payload.provider, error=str(exc))
        raise ServiceUnavailableError(f"Provider '{payload.provider}' failed: {exc}") from exc

    return ChatResponse(
        content="".join(parts),
        provider=payload.provider,
        model=model,
        finish_reason="stop",
    )


# ---------------------------------------------------------------------------
# Phase 3+ stub — kept so the route is registered for future routing logic
# ---------------------------------------------------------------------------


@router.post("/completions", summary="Routing-aware chat completions (Phase 3+)")
async def chat_completions() -> dict:
    return {"message": "Smart routing is implemented in Phase 3."}
