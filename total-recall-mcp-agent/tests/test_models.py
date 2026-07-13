"""
Tests for MCP Database models
"""

from app.database.models.base import Base
from app.database.models.user import User


def test_base_model():
    """
    Testing Base Model for MCP DB
    """
    assert Base is not None


def test_user_model():
    """
    Testing User Model for MCP DB
    """
    user = User(
        email="john.doe@example.com",
        first_name="John",
        last_name="Doe",
    )

    assert user.email == "john.doe@example.com"
    assert user.first_name == "John"
    assert user.last_name == "Doe"
