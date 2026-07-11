# from mcp.server.fastmcp import FastMCP

# mcp = FastMCP("Total-Recall MCP Agent")

# from app.tools.health import register_health_tools
# from app.tools.users import register_user_tools
# from app.tools.sql import register_sql_tools

# register_health_tools(mcp)
# register_user_tools(mcp)
# register_sql_tools(mcp)

from mcp.server.fastmcp import FastMCP

from app.core.logging import logger
from app.mcp.registry import register_tools

mcp = FastMCP(name="total-recall-mcp-agent")


def create_mcp_server() -> FastMCP:
    """
    Create and configure Total-Recall MCP server.
    """

    logger.info("creating_total-recall-mcp_server", name="total-recall-mcp-agent")

    register_tools(mcp)

    return mcp
