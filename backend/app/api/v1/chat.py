"""Chat completions endpoints — Phase 4 (routing-aware + request logging).

Phase 6 additions:
  - Rate limiting (Redis fixed-window, RateLimitService)
  - Prompt caching (Redis, CacheService)
  - Provider fallback (try next candidate on primary failure)
"""

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
from app.services.cache_service import CacheService
from app.services.rate_limit_service import RateLimitService
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


def _build_fallback_decision(
    routing_result: RoutingResult,
    fallback_provider_id: str,
    fallback_model: str,
) -> RoutingDecision:
    """Build a routing decision schema reflecting the fallback provider used."""
    return RoutingDecision(
        strategy=routing_result.strategy,
        selected=f"{fallback_provider_id}/{fallback_model}",
        reason=f"Fallback from {routing_result.selected_provider_id} — primary provider unavailable",
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
            for c in routing_result.candidates
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


def _ordered_candidates(routing_result: RoutingResult) -> list[tuple[str, str]]:
    """Return (provider_id, model_id) pairs: primary first, then healthy fallbacks."""
    primary = (routing_result.selected_provider_id, routing_result.selected_model)
    fallbacks = [
        (c.provider_id, c.model_id)
        for c in routing_result.candidates
        if c.provider_id != routing_result.selected_provider_id and c.health != "down"
    ]
    return [primary, *fallbacks]


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
    fallback_collector: list[str],
) -> AsyncGenerator[str, None]:
    """Stream tokens from the selected provider, trying fallbacks on failure."""
    registry = get_registry()
    candidates = _ordered_candidates(routing_result)
    last_error: str = "Unknown error"

    for attempt, (provider_id, model_id) in enumerate(candidates[:2]):  # max 2 attempts
        try:
            provider = registry.get(provider_id)
        except Exception as exc:
            last_error = str(exc)
            continue

        normalized = provider.normalize_request(
            messages=req_body["messages"],
            model=model_id,
            max_tokens=req_body.get("max_tokens", 1024),
            temperature=req_body.get("temperature", 0.7),
        )
        normalized["stream"] = True

        try:
            async for token in provider.call(normalized):
                response_collector.append(token)
                yield f"data: {json.dumps({'type': 'delta', 'content': token})}\n\n"

            # Success — build final routing schema
            if attempt > 0:
                fallback_collector.append(provider_id)
                routing_schema = _build_fallback_decision(routing_result, provider_id, model_id)
            else:
                routing_schema = _routing_result_to_schema(routing_result)

            done_payload = {
                "type": "done",
                "provider": provider_id,
                "model": model_id,
                "finish_reason": "stop",
                "routing_decision": routing_schema.model_dump(),
                "cache_hit": False,
                "fallback_provider": provider_id if attempt > 0 else None,
            }
            yield f"data: {json.dumps(done_payload)}\n\n"
            return

        except Exception as exc:
            if response_collector:
                # Tokens already sent — cannot fallback mid-stream
                error_collector.append(str(exc))
                log.error("provider_stream_error_mid", provider=provider_id, error=str(exc))
                yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
                return
            last_error = str(exc)
            log.warning(
                "provider_failed_trying_fallback",
                provider=provider_id,
                attempt=attempt,
                error=str(exc),
            )

    # All candidates exhausted
    error_collector.append(last_error)
    log.error("all_providers_failed", error=last_error)
    yield f"data: {json.dumps({'type': 'error', 'message': last_error})}\n\n"


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
    Rate-limited, cached, streaming chat endpoint.

    SSE event shapes::

        data: {"type": "delta",  "content": "token text"}
        data: {"type": "done",   "provider": "openai", "model": "gpt-4o-mini",
                                  "finish_reason": "stop", "routing_decision": {...},
                                  "cache_hit": false, "fallback_provider": null}
        data: {"type": "error",  "message": "reason"}
    """
    # 1. Rate limit
    rate_svc = RateLimitService()
    await rate_svc.check_and_increment(user.id)

    # 2. Route
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

    # 3. Cache check
    cache_svc = CacheService()
    cache_key = cache_svc.build_key(
        prompt, routing_result.selected_model, payload.temperature, payload.max_tokens
    )
    cached_content = await cache_svc.get(cache_key)

    if cached_content is not None:
        log.info("cache_hit", key=cache_key)

        async def cached_event_generator() -> AsyncGenerator[str, None]:
            yield f"data: {json.dumps({'type': 'delta', 'content': cached_content})}\n\n"
            done_payload = {
                "type": "done",
                "provider": routing_result.selected_provider_id,
                "model": routing_result.selected_model,
                "finish_reason": "stop",
                "routing_decision": routing_schema.model_dump(),
                "cache_hit": True,
                "fallback_provider": None,
            }
            yield f"data: {json.dumps(done_payload)}\n\n"
            # Fire-and-forget logging for cache hit
            asyncio.create_task(
                _log_request_bg(
                    user_id=user.id,
                    prompt=prompt,
                    response_text=cached_content,
                    provider=routing_result.selected_provider_id,
                    model=routing_result.selected_model,
                    routing_strategy=routing_result.strategy,
                    routing_decision_dict=routing_schema.model_dump(),
                    routing_reason=routing_result.reason,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=_estimate_tokens(cached_content),
                    latency_ms=0,
                    error_message=None,
                    conversation_id=payload.conversation_id,
                )
            )

        return StreamingResponse(
            cached_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    # 4. Stream from provider
    response_collector: list[str] = []
    error_collector: list[str] = []
    fallback_collector: list[str] = []
    start_time = time.monotonic()

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for chunk in _run_stream(
                routing_result, req_body, response_collector, error_collector, fallback_collector
            ):
                if await request.is_disconnected():
                    if not error_collector:
                        error_collector.append("Client disconnected")
                    break
                yield chunk
        finally:
            latency_ms = int((time.monotonic() - start_time) * 1_000)
            response_text = "".join(response_collector)
            actual_provider = fallback_collector[0] if fallback_collector else routing_result.selected_provider_id

            # Cache successful responses
            if response_text and not error_collector:
                await cache_svc.set(cache_key, response_text)

            asyncio.create_task(
                _log_request_bg(
                    user_id=user.id,
                    prompt=prompt,
                    response_text=response_text,
                    provider=actual_provider,
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
    """Rate-limited, cached, non-streaming chat endpoint with provider fallback."""
    # 1. Rate limit
    rate_svc = RateLimitService()
    await rate_svc.check_and_increment(user.id)

    # 2. Route
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

    # 3. Cache check
    cache_svc = CacheService()
    cache_key = cache_svc.build_key(
        prompt, routing_result.selected_model, payload.temperature, payload.max_tokens
    )
    cached_content = await cache_svc.get(cache_key)

    if cached_content is not None:
        log.info("cache_hit", key=cache_key)
        asyncio.create_task(
            _log_request_bg(
                user_id=user.id,
                prompt=prompt,
                response_text=cached_content,
                provider=routing_result.selected_provider_id,
                model=routing_result.selected_model,
                routing_strategy=routing_result.strategy,
                routing_decision_dict=routing_schema.model_dump(),
                routing_reason=routing_result.reason,
                prompt_tokens=prompt_tokens,
                completion_tokens=_estimate_tokens(cached_content),
                latency_ms=0,
                error_message=None,
                conversation_id=payload.conversation_id,
            )
        )
        return ChatResponse(
            content=cached_content,
            provider=routing_result.selected_provider_id,
            model=routing_result.selected_model,
            finish_reason="stop",
            routing_decision=routing_schema,
            cache_hit=True,
        )

    # 4. Call provider with fallback
    registry = get_registry()
    messages = [m.model_dump() for m in payload.messages]
    candidates = _ordered_candidates(routing_result)

    start_time = time.monotonic()
    response_text = ""
    error_msg: str | None = None
    actual_provider_id = routing_result.selected_provider_id
    actual_model_id = routing_result.selected_model
    used_fallback = False
    last_error: str | None = None

    for attempt, (provider_id, model_id) in enumerate(candidates[:2]):
        try:
            provider = registry.get(provider_id)
        except Exception as exc:
            last_error = str(exc)
            continue

        normalized = provider.normalize_request(
            messages=messages,
            model=model_id,
            max_tokens=payload.max_tokens,
            temperature=payload.temperature,
        )
        normalized["stream"] = False

        parts: list[str] = []
        try:
            async for chunk in provider.call(normalized):
                parts.append(chunk)
            response_text = "".join(parts)
            actual_provider_id = provider_id
            actual_model_id = model_id
            used_fallback = attempt > 0
            error_msg = None
            break  # success
        except Exception as exc:
            last_error = str(exc)
            if attempt < len(candidates[:2]) - 1:
                log.warning("provider_failed_trying_fallback", provider=provider_id, error=str(exc))
            else:
                error_msg = last_error

    latency_ms = int((time.monotonic() - start_time) * 1_000)

    if error_msg is None and not response_text and last_error:
        error_msg = last_error

    # Build routing decision reflecting what actually happened
    if used_fallback:
        final_schema = _build_fallback_decision(routing_result, actual_provider_id, actual_model_id)
    else:
        final_schema = routing_schema

    asyncio.create_task(
        _log_request_bg(
            user_id=user.id,
            prompt=prompt,
            response_text=response_text,
            provider=actual_provider_id,
            model=actual_model_id,
            routing_strategy=routing_result.strategy,
            routing_decision_dict=final_schema.model_dump(),
            routing_reason=final_schema.reason,
            prompt_tokens=prompt_tokens,
            completion_tokens=_estimate_tokens(response_text),
            latency_ms=latency_ms,
            error_message=error_msg,
            conversation_id=payload.conversation_id,
        )
    )

    if error_msg:
        log.error("all_providers_failed", error=error_msg)
        raise ServiceUnavailableError(f"All providers failed: {error_msg}")

    # Cache successful response
    await cache_svc.set(cache_key, response_text)

    return ChatResponse(
        content=response_text,
        provider=actual_provider_id,
        model=actual_model_id,
        finish_reason="stop",
        routing_decision=final_schema,
        cache_hit=False,
        fallback_provider=actual_provider_id if used_fallback else None,
    )


@router.post("/completions", summary="Alias — use /chat/stream for streaming")
async def chat_completions() -> dict:
    return {"message": "Use POST /api/v1/chat/stream for streaming or POST /api/v1/chat for non-streaming."}
