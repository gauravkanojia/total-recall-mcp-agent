"""
User MCP tools.
"""

from app.mcp.executor import executor
from app.services.user_service import UserService


async def get_user(
    context,
):
    """
    Return the calling principal's user record.
    """

    service = UserService(context.db_session)

    return await service.get_user_by_principal(context.principal_id)


def register_user_tools() -> None:
    """
    Register user MCP tools.
    """

    executor.register(
        "get_user",
        get_user,
    )
