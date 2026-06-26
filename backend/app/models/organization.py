"""Organization ORM model."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class Organization(Base, UUIDMixin, TimestampMixin):
    """
    A tenant organization that owns API keys and groups users.

    Every API key belongs to an organization.  Users join organizations
    through ``Membership`` records with a role assignment.
    """

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    # Relationships
    memberships: Mapped[list["Membership"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Membership", back_populates="organization", cascade="all, delete-orphan", lazy="select"
    )
    api_keys: Mapped[list["APIKey"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "APIKey", back_populates="organization", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Organization id={self.id!s} slug={self.slug!r}>"
