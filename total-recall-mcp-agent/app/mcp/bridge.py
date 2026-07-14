"""
FastMCP bridge.

Connects FastMCP exposed tools
to internal executor tools.
"""

from app.mcp.executor import executor
from app.mcp.server import get_mcp_server


async def _execute_tool(name: str, **kwargs):
    """Run an internal tool handler."""

    return await executor.execute(name, **kwargs)


def register_mcp_tools() -> None:
    """
    Register public MCP tools.
    """

    mcp_server = get_mcp_server()

    @mcp_server.tool()
    async def health_check() -> dict:
        return await _execute_tool("health_check")

    @mcp_server.tool()
    async def get_user(
        email: str,
    ) -> dict | None:
        return await _execute_tool(
            "get_user",
            email=email,
        )

    @mcp_server.tool()
    async def remember_memory(
        content: str,
        kind: str = "fact",
        metadata: dict | None = None,
    ) -> dict:
        return await _execute_tool(
            "remember_memory",
            content=content,
            kind=kind,
            metadata=metadata,
        )

    @mcp_server.tool()
    async def recall_memory(
        query: str,
        kind: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        return await _execute_tool(
            "recall_memory",
            query=query,
            kind=kind,
            limit=limit,
        )
