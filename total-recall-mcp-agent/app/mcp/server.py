"""
MCP Server bootstrap.
"""

from mcp.server.fastmcp import FastMCP

from app.core.logging import logger

mcp_server = FastMCP(
    name="total-recall-mcp-agent",
    instructions="""
    MCP server for interacting with users,
    database operations, and AI agent workflows.
    """,
)


def get_mcp_server() -> FastMCP:
    """
    Get MCP server instance.
    """

    logger.info("creating_total-recall-mcp_server", name="total-recall-mcp-agent")
    return mcp_server
