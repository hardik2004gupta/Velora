"""Request ORM model — immutable audit log of every inference call."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDMixin


class Request(Base, UUIDMixin):
    """Immutable record of a single LLM inference request."""

    __tablename__ = "requests"

    # Human-readable request ID (req_<16 hex chars>)
    request_id: Mapped[str | None] = mapped_column(
        String(24), nullable=True, unique=True, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    conversation_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    # Prompt text (last user message) and full response text
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)

    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    routing_strategy: Mapped[str] = mapped_column(String(20), nullable=False)
    # Plain-text routing explanation (mirrors routing_decision.reason)
    routing_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cache_hit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    routing_decision: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    user: Mapped["User"] = relationship("User", back_populates="requests")  # type: ignore[name-defined]  # noqa: F821

    def __repr__(self) -> str:
        return f"<Request id={self.id!s} request_id={self.request_id!r} provider={self.provider!r} status={self.status!r}>"
