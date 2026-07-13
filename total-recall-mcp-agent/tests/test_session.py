"""
Tests for Database Session Manager
"""

from app.database.session import get_session_factory


def test_db_session_factory_exists():
    """
    beta
    """
    assert get_session_factory is not None
