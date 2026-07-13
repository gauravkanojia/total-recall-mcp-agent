"""
MCP middleware utilities.

Handles MCP's Cross-cutting lifecycle concerns around MCP tool execution.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from uuid import uuid4
from app.mcp.context import MCPContext
from app.auth.mcp_auth import validate_mcp_token
from app.database.session import get_session_factory


@asynccontextmanager
async def mcp_context_manager(
    token: str | None = None,
) -> AsyncGenerator[MCPContext, None]:
    """
    Create and manage MCP execution context.
    """

    session_factory = get_session_factory()

    async with session_factory() as session:
        principal = None

        if token:
            principal = validate_mcp_token(token)

        context = MCPContext(
            db_session=session,
            request_id=str(uuid4()),
            cognito_sub=(principal.cognito_sub if principal else None),
        )

        yield context
    # session = session_factory()

    # context = MCPContext(
    #     request_id=str(uuid4()),
    #     db_session=session,
    # )

    # token = set_context(context)

    # try:
    #     yield context

    # finally:
    #     clear_context(token)

    #     await session.close()
