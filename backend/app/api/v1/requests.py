"""Request history endpoints — Phase 4."""

from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.core.exceptions import NotFoundError
from app.database.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.request_repository import RequestRepository
from app.schemas.request import RequestDetail, RequestListResponse, RequestSummary

router = APIRouter()


# Export must be registered BEFORE /{request_id} to prevent FastAPI treating
# the literal "export" as a path parameter.


@router.get("/export", summary="Export request history as CSV or JSON")
async def export_requests(
    format: str = Query(default="json", pattern="^(json|csv)$"),
    provider: str | None = Query(default=None),
    status: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """Download the authenticated user's full request history."""
    repo = RequestRepository(db)
    rows = await repo.list_all_for_export(user.id, provider=provider, status=status)

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "request_id", "created_at", "provider", "model", "routing_strategy",
            "prompt_tokens", "completion_tokens", "total_tokens", "cost_usd",
            "latency_ms", "status", "cache_hit", "conversation_id", "prompt",
        ])
        for r in rows:
            writer.writerow([
                r.request_id,
                r.created_at.isoformat(),
                r.provider,
                r.model,
                r.routing_strategy,
                r.prompt_tokens,
                r.completion_tokens,
                r.total_tokens,
                float(r.cost_usd or 0),
                r.latency_ms,
                r.status,
                r.cache_hit,
                r.conversation_id,
                (r.prompt or "")[:500],
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=velora_requests.csv"},
        )

    data = [
        {
            "request_id": r.request_id,
            "created_at": r.created_at.isoformat(),
            "provider": r.provider,
            "model": r.model,
            "routing_strategy": r.routing_strategy,
            "conversation_id": r.conversation_id,
            "prompt": r.prompt,
            "response": r.response,
            "prompt_tokens": r.prompt_tokens,
            "completion_tokens": r.completion_tokens,
            "total_tokens": r.total_tokens,
            "cost_usd": float(r.cost_usd or 0),
            "latency_ms": r.latency_ms,
            "status": r.status,
            "cache_hit": r.cache_hit,
            "error_message": r.error_message,
            "routing_reason": r.routing_reason,
        }
        for r in rows
    ]
    return StreamingResponse(
        iter([json.dumps(data, indent=2)]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=velora_requests.json"},
    )


@router.get("/{request_id}", response_model=RequestDetail, summary="Get full request detail")
async def get_request(
    request_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RequestDetail:
    """Return the full record for a single request, including prompt, response, and routing decision."""
    repo = RequestRepository(db)
    record = await repo.get_by_request_id(request_id, user.id)
    if record is None:
        raise NotFoundError(f"Request '{request_id}' not found.")
    return RequestDetail.model_validate(record)


@router.get("", response_model=RequestListResponse, summary="List request history with filtering")
async def list_requests(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    provider: str | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
    sort_by: str = Query(
        default="created_at",
        pattern="^(created_at|latency_ms|cost_usd|provider)$",
    ),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RequestListResponse:
    """
    Return paginated request history for the authenticated user.

    - ``search``: matched against request_id, prompt, and provider
    - ``sort_by``: one of created_at | latency_ms | cost_usd | provider
    - ``sort_dir``: asc | desc
    """
    repo = RequestRepository(db)
    rows, total = await repo.list_for_user(
        user.id,
        page=page,
        limit=limit,
        provider=provider,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    items = [RequestSummary.model_validate(r) for r in rows]
    return RequestListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        has_next=(page * limit) < total,
    )
