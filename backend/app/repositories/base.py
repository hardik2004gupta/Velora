"""
Generic async repository base class.

Provides standard CRUD operations for any SQLAlchemy model.
Concrete repositories inherit and add domain-specific query methods.
"""

from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic CRUD repository for an ORM model.

    Concrete repositories should inherit from this and declare the model
    type explicitly::

        class UserRepository(BaseRepository[User]):
            model = User
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        """Return a record by primary key, or None if not found."""
        return await self._session.get(self.model, entity_id)

    async def get_all(self) -> list[ModelT]:
        """Return all records for this model (use with caution on large tables)."""
        result = await self._session.execute(select(self.model))
        return list(result.scalars().all())

    async def add(self, entity: ModelT) -> ModelT:
        """Persist a new entity and flush to get the DB-assigned ID."""
        self._session.add(entity)
        await self._session.flush()
        return entity

    async def delete(self, entity: ModelT) -> None:
        """Delete an entity from the database."""
        await self._session.delete(entity)
        await self._session.flush()
