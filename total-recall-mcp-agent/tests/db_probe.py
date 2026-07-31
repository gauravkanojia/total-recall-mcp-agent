"""
Probe whether settings.DATABASE_URL accepts connections.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.database.database import get_engine

_db_reachable: bool | None = None


async def _probe_database_connection() -> bool:
    engine = get_engine()

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except OSError:
        return False
    except Exception:  # noqa: BLE001 — any driver/SSL/auth failure means unreachable
        return False
    finally:
        await engine.dispose()
        get_engine.cache_clear()


def database_is_reachable() -> bool:
    """
    Return True when DATABASE_URL accepts a connection.

    Result is cached for the pytest process.
    """

    global _db_reachable

    if _db_reachable is not None:
        return _db_reachable

    try:
        _db_reachable = asyncio.run(_probe_database_connection())
    except Exception:  # noqa: BLE001
        _db_reachable = False

    return _db_reachable
