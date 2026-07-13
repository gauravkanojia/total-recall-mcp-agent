"""
Test DB Engine creation
"""

from sqlalchemy.ext.asyncio import AsyncEngine

from app.database.database import get_engine


def test_db_engine_creation():
    """
    beta
    """
    engine = get_engine()

    assert isinstance(engine, AsyncEngine)
