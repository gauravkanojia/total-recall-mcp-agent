"""
Fixtures for DATABASE_URL-backed integration tests.
"""

import pytest
import pytest_asyncio
from db_probe import database_is_reachable

from app.database.models.user import User
from app.database.session import get_session_factory
from app.identity.principal import DEFAULT_PRINCIPAL_ID


@pytest.fixture(scope="session", autouse=True)
def require_reachable_database():
    if not database_is_reachable():
        pytest.skip("DATABASE_URL is not reachable", allow_module_level=True)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def seed_integration_user():
    """
    Ensure the default local principal exists for get_user integration tests.
    """

    session_factory = get_session_factory()

    async with session_factory() as session:
        existing = await session.execute(
            User.__table__.select().where(User.principal_id == DEFAULT_PRINCIPAL_ID)
        )

        if existing.first():
            return

        session.add(
            User(
                email="test@example.com",
                first_name="Test",
                last_name="User",
                principal_id=DEFAULT_PRINCIPAL_ID,
            )
        )
        await session.commit()
