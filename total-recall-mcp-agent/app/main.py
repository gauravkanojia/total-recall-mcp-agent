"""
ASGI entry point for containerized deployments (Docker/ECS).

Serves the same MCP tools as ``app.cli``, but over Streamable HTTP so
the agent can be reached as a network service (e.g. behind an AWS ALB)
instead of being spawned as a local stdio subprocess.

Run with: uv run uvicorn app.main:app --host 0.0.0.0 --port 4646
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.bootstrap import bootstrap_mcp_server
from app.core.config import settings
from app.core.logging import logger, setup_logging

setup_logging()

mcp_server = bootstrap_mcp_server()

# FastMCP's Streamable HTTP app serves its own "/mcp" route by default.
# Mounting that under another "/mcp" prefix would double up the path
# (.../mcp/mcp), so the sub-app is pinned to "/" and mounted at "/mcp"
# below, giving a single, predictable "/mcp" endpoint.
mcp_server.settings.streamable_http_path = "/"
mcp_asgi_app = mcp_server.streamable_http_app()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """
    Start/stop the MCP session manager alongside the FastAPI app.

    Required for Streamable HTTP: without an active session manager the
    mounted MCP routes accept connections but never respond.
    """

    async with mcp_server.session_manager.run():
        logger.info("mcp_http_transport_ready", path="/mcp")
        yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.mount("/mcp", mcp_asgi_app)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Liveness probe for the ECS/ALB health check."""

    return {"status": "ok", "service": settings.APP_NAME}
