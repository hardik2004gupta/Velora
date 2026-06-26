"""Membership ORM model — user ↔ organization join table with role."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDMixin


class Membership(Base, UUIDMixin):
    """
    Associates a User with an Organization and assigns their role.

    A user can belong to multiple organizations with different roles in each.
    A user may only have one membership per organization (unique constraint on
    user_id + organization_id).
    """

    __tablename__ = "memberships"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="developer")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="memberships")  # type: ignore[name-defined]  # noqa: F821
    organization: Mapped["Organization"] = relationship("Organization", back_populates="memberships")  # type: ignore[name-defined]  # noqa: F821

    def __repr__(self) -> str:
        return f"<Membership user={self.user_id!s} org={self.organization_id!s} role={self.role!r}>"
