"""
Get DB Engine using SQLAlchemy
"""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.logging import logger


def _require_tls_in_production() -> None:
    """
    Refuse to boot production against a non-TLS database URL.
    """

    if (
        settings.ENVIRONMENT == "production"
        and "sslmode=verify-full" not in settings.DATABASE_URL
    ):
        raise RuntimeError(
            "ENVIRONMENT=production requires DATABASE_URL with sslmode=verify-full "
            "(TLS with certificate verification)."
        )


@lru_cache
def get_engine() -> AsyncEngine:
    """
    Create and cache the SQLAlchemy async engine.

    A single engine should exist for the lifetime of the application.
    Connections are pooled by default; DATABASE_USE_NULLPOOL=true (tests)
    opens a fresh connection per session instead.
    """

    _require_tls_in_production()

    logger.info(
        "creating_database_engine",
        database=settings.DATABASE_NAME,
        pooling="nullpool" if settings.DATABASE_USE_NULLPOOL else "pooled",
    )

    if settings.DATABASE_USE_NULLPOOL:
        return create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            poolclass=NullPool,
        )

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
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
