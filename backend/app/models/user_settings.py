"""UserSettings ORM model — per-user preferences (1:1 with User)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDMixin


class UserSettings(Base, UUIDMixin):
    """User-level preferences stored server-side."""

    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    default_routing_strategy: Mapped[str] = mapped_column(
        String(20), nullable=False, default="auto"
    )
    default_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    theme: Mapped[str] = mapped_column(String(10), nullable=False, default="dark")
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=2048)
    temperature: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, default=0.70)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="settings")  # type: ignore[name-defined]  # noqa: F821

    def __repr__(self) -> str:
        return f"<UserSettings user_id={self.user_id!s}>"
