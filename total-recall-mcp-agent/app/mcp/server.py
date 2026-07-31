"""
MCP server bootstrap.
"""

from mcp.server.fastmcp import FastMCP
from sqlalchemy import text
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import logger
from app.database.database import get_engine

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
        # Stateless HTTP: each POST is self-contained, so tool handlers run
        # inside the request task (required for the auth middleware's
        # request-scoped principal to propagate) and any ECS task behind the
        # ALB can serve any request.
        stateless_http=True,
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

    @server.custom_route("/ready", methods=["GET"])
    async def http_ready(_request: Request) -> JSONResponse:
        """Readiness probe: verifies the database answers, not just the process."""

        try:
            engine = get_engine()
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001 — any DB failure means not ready
            logger.warning("readiness_check_failed", error=str(exc))
            return JSONResponse(
                {"status": "unavailable", "service": settings.APP_NAME},
                status_code=503,
            )

        return JSONResponse(
            {
                "status": "ready",
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
