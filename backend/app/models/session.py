"""Session ORM model — stores refresh tokens for secure JWT rotation."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDMixin


class Session(Base, UUIDMixin):
    """
    Persistent session record that backs a refresh token.

    The ``refresh_token_hash`` is a SHA-256 hex digest of the opaque token
    string sent to the client — the raw token is never stored.

    On logout or rotation, the session row is deleted, which immediately
    invalidates the old refresh token.
    """

    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Optional: track the device / IP for the sessions UI
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")  # type: ignore[name-defined]  # noqa: F821

    def __repr__(self) -> str:
        return f"<Session id={self.id!s} user={self.user_id!s}>"
