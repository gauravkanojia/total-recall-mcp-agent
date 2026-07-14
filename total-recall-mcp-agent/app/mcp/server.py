"""
MCP server bootstrap.
"""

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import logger

_mcp_server: FastMCP | None = None


def _create_mcp_server() -> FastMCP:
    settings = get_settings()

    server = FastMCP(
        name="total-recall-mcp-agent",
        instructions="""
    MCP server for interacting with users,
    database operations, and AI agent workflows.
    """,
        host=settings.HOST,
        port=settings.PORT,
        streamable_http_path="/mcp",
    )

    @server.custom_route("/health", methods=["GET"])
    async def http_health(_request: Request) -> JSONResponse:
        """Liveness probe for ALB / container orchestrators."""

        return JSONResponse(
            {
                "status": "ok",
                "service": settings.APP_NAME,
            }
        )

    return server


def get_mcp_server() -> FastMCP:
    """Return the shared FastMCP server instance."""

    global _mcp_server  # pylint: disable=global-statement

    if _mcp_server is None:
        _mcp_server = _create_mcp_server()
        logger.info("creating_total-recall-mcp-agent_server", name="total-recall-mcp-agent")

    return _mcp_server
