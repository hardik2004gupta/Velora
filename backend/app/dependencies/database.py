"""Database session dependency."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session

# Re-export for convenient importing in route files
DBSession = Depends(get_db_session)


async def get_db(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an ``AsyncSession``.

    This is a thin wrapper that routes use as ``Depends(get_db)``.
    """
    yield session
