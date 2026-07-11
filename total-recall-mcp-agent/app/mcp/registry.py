# register tools

# health
# users
# sql

from mcp.server.fastmcp import FastMCP

from app.tools.health import register_health_tools


def register_tools(
    mcp: FastMCP,
) -> None:
    """
    Register all MCP tools.
    """

    register_health_tools(mcp)
