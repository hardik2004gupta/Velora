"""
Declarative base and shared mixin for all ORM models.

Every model should inherit from ``Base``.  Models that need standard audit
columns (``id``, ``created_at``, ``updated_at``) should also inherit from
``TimestampMixin``.

Example::

    from app.database.base import Base, TimestampMixin

    class User(Base, TimestampMixin):
        __tablename__ = "users"
        ...
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base class shared by all ORM models."""

    # Subclasses must define __tablename__
    pass


class UUIDMixin:
    """Adds a UUID primary key column named ``id``."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` columns with automatic management."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )
