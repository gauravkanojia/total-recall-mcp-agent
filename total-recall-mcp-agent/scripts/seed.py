"""
Database seed script.
"""

import asyncio

from app.database.session import session_factory
from app.database.models.user import User


async def seed_users():

    async with session_factory() as session:
        existing = await session.execute(
            User.__table__.select().where(User.email == "test@example.com")
        )

        if existing.first():
            print("User already exists")
            return

        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            cognito_sub="local-test-user",
        )

        session.add(user)

        await session.commit()

        print(f"Created user: {user.email}")


if __name__ == "__main__":
    asyncio.run(seed_users())
