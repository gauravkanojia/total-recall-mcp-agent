from mcp.server.fastmcp import FastMCP


def register_health_tools(
    mcp: FastMCP,
) -> None:
    """
    Register health-related MCP tools.
    """

    @mcp.tool()
    async def health() -> dict:
        """
        Check MCP server health.
        """

        return {"status": "MCP server is healthy"}
