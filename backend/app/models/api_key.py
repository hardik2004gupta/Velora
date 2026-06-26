"""APIKey ORM model — scoped to an Organization."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDMixin


class APIKey(Base, UUIDMixin):
    """
    Programmatic access key scoped to a single Organization.

    Key security model:
    - The full key is returned ONCE at creation — never stored in plaintext.
    - ``key_prefix`` (first 8 chars) is stored for UI display and fast lookup.
    - ``hashed_key`` is a bcrypt hash of the full key for verification.
    - ``revoked`` is set to True instead of deleting rows (audit trail).
    """

    __tablename__ = "api_keys"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    hashed_key: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="developer")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Organization", back_populates="api_keys"
    )

    @property
    def is_active(self) -> bool:
        """Return True if the key is not revoked and not expired."""
        from datetime import UTC
        if self.revoked:
            return False
        if self.expires_at and self.expires_at < datetime.now(UTC):
            return False
        return True

    def __repr__(self) -> str:
        return f"<APIKey id={self.id!s} prefix={self.key_prefix!r} revoked={self.revoked}>"
