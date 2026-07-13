"""
User MCP tools.
"""

from app.mcp.executor import executor
from app.services.user_service import UserService


async def get_user(
    email: str,
    context,
):
    """
    Retrieve user by email.
    """

    service = UserService(context.db_session)

    return await service.get_user(email)


def register_user_tools() -> None:
    """
    Register user MCP tools.
    """

    executor.register(
        "get_user",
        get_user,
    )
