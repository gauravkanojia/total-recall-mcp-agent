"""
FastMCP bridge.

Connects FastMCP exposed tools
to internal executor tools.
"""

from app.mcp.executor import executor
from app.mcp.server import mcp_server


def register_mcp_tools() -> None:
    """
    Register public MCP tools.
    """

    @mcp_server.tool()
    async def health_check() -> dict:
        return await executor.execute(
            "health_check",
        )

    @mcp_server.tool()
    async def get_user(
        email: str,
    ) -> dict | None:

        return await executor.execute(
            "get_user",
            email=email,
        )
