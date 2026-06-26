"""
Async session factory and FastAPI dependency.

Usage in a route::

    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.database.session import get_db_session

    @router.get("/example")
    async def example(db: AsyncSession = Depends(get_db_session)):
        ...
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database.engine import engine

# Session factory — creates new sessions bound to our engine.
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keep attributes accessible after commit
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an ``AsyncSession``.

    The session is automatically committed on success or rolled back on any
    exception, then closed when the request is complete.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
