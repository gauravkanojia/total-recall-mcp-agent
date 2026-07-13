from app.repositories.user_repository import UserRepository


class UserService:
    """
    User business logic.
    """

    def __init__(self, session):
        self.repository = UserRepository(session)

    async def get_user(
        self,
        email: str,
    ) -> dict | None:

        user = await self.repository.get_by_email(email)

        if not user:
            return None

        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
        }
