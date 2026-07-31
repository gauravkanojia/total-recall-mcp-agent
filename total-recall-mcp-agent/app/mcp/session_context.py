"""
MCP session context lifecycle.

Opens a database session and builds request-scoped MCPContext for tool execution.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import uuid4

from app.database.session import get_session_factory
from app.identity.principal import resolve_mcp_principal
from app.mcp.context import MCPContext


@asynccontextmanager
async def mcp_session_context() -> AsyncGenerator[MCPContext]:
    """
    Create and manage MCP execution context.
    """

    session_factory = get_session_factory()
    principal = resolve_mcp_principal()

    async with session_factory() as session:
        context = MCPContext(
            db_session=session,
            request_id=str(uuid4()),
            principal_id=principal.principal_id,
        )

        yield context
