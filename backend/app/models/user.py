"""User ORM model."""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """Represents an authenticated Velora user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Session", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    requests: Mapped[list["Request"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Request", back_populates="user", lazy="select"
    )
    settings: Mapped["UserSettings | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "UserSettings", back_populates="user", uselist=False, lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!s} email={self.email!r}>"
