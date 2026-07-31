from app.repositories.user_repository import UserRepository


class UserService:
    """
    User business logic.
    """

    def __init__(self, session):
        self.repository = UserRepository(session)

    async def get_user_by_principal(
        self,
        principal_id: str | None,
    ) -> dict | None:
        """
        Return the caller's own user record (scoped by principal).
        """

        if not principal_id:
            return None

        user = await self.repository.get_by_principal_id(principal_id)

        if not user:
            return None

        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "principal_id": user.principal_id,
        }
