"""
Tests for User Pydantic Schemas
"""

from app.schemas.user import UserCreate


def test_user_create():
    """
    Test User Pydantic Schema creation
    """

    user = UserCreate(
        email="john.doe@example.com",
        first_name="John",
        last_name="Doe",
    )

    assert user.email == "john.doe@example.com"
