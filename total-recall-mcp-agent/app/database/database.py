"""
Get DB Engine using SQLAlchemy
"""

from functools import lru_cache

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.logging import logger

# libpq-style sslmode values that mean "encrypt and verify the server cert
# against a trusted CA" — everything asyncpg needs is covered by its
# default SSL context (ssl=True), which does hostname + CA verification.
_TLS_SSLMODES = {"require", "verify-ca", "verify-full"}


def _require_tls_in_production() -> None:
    """
    Refuse to boot production against a non-TLS database URL.
    """

    if settings.ENVIRONMENT == "production" and "sslmode=verify-full" not in settings.DATABASE_URL:
        raise RuntimeError(
            "ENVIRONMENT=production requires DATABASE_URL with sslmode=verify-full "
            "(TLS with certificate verification)."
        )


def _url_and_connect_args() -> tuple[str, dict]:
    """
    Split the libpq-style ``sslmode`` query param out of DATABASE_URL.

    asyncpg's connect() has no ``sslmode`` keyword (that's a
    psycopg2/libpq-ism), so SQLAlchemy's asyncpg dialect fails with
    "connect() got an unexpected keyword argument 'sslmode'" if it's left
    in the URL's query string. Translate it into the ``ssl`` connect_args
    asyncpg actually understands instead.
    """

    url = make_url(settings.DATABASE_URL)
    sslmode = url.query.get("sslmode")
    if sslmode is None:
        return settings.DATABASE_URL, {}

    url = url.difference_update_query({"sslmode"})
    connect_args = {"ssl": True} if sslmode in _TLS_SSLMODES else {}
    return url.render_as_string(hide_password=False), connect_args


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

    url, connect_args = _url_and_connect_args()

    if settings.DATABASE_USE_NULLPOOL:
        return create_async_engine(
            url,
            echo=settings.DATABASE_ECHO,
            poolclass=NullPool,
            connect_args=connect_args,
        )

    return create_async_engine(
        url,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        connect_args=connect_args,
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
