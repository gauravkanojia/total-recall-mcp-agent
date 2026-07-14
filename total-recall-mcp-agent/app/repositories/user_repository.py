"""
User repository
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.schemas.user import UserCreate


class UserRepository:
    """
    Repository for User persistence operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, payload: UserCreate) -> User:
        """
        Create a new user.
        """

        user = User(
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            principal_id=payload.principal_id,
        )

        self._session.add(user)

        # Flush sends the INSERT without committing the transaction.
        await self._session.flush()
        await self._session.refresh(user)

        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        """
        Retrieve a user by ID.
        """

        statement = select(User).where(User.id == user_id)

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by email.
        """

        statement = select(User).where(User.email == email)

        result = await self._session.execute(statement)

        return result.scalar_one_or_none()

    async def list(self) -> list[User]:
        """
        Return all users.
        """

        statement = select(User).order_by(User.created_at)

        result = await self._session.execute(statement)

        return list(result.scalars().all())

    async def delete(self, user: User) -> None:
        """
        Delete a user.
        """

        await self._session.delete(user)
