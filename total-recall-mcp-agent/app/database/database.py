"""
Get DB Engine using SQLAlchemy
"""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.logging import logger


@lru_cache
def get_engine() -> AsyncEngine:
    """
    Create and cache the SQLAlchemy async engine.

    A single engine should exist for the lifetime of the application.
    """

    logger.info("creating_database_engine", database=settings.DATABASE_NAME)

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,
        pool_recycle=1800,
        poolclass=NullPool,
    )


async def dispose_engine() -> None:
    """
    Dispose SQLAlchemy engine.

    Used primarily by tests to avoid
    cross-event-loop connection reuse.
    """

    if get_engine.cache_info().currsize:
        engine = get_engine()
        await engine.dispose()
        get_engine.cache_clear()
