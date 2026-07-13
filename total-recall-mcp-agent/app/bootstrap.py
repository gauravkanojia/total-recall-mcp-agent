"""
Application bootstrap.

Both entry points into the agent -- the standalone stdio process
(``app.cli``) and the HTTP/ASGI process (``app.main``) -- need the exact
same MCP tools registered before the server can do anything useful.
This module is the single place that wires that up, so the two entry
points can never drift out of sync.
"""

from mcp.server.fastmcp import FastMCP

from app.core.logging import logger
from app.mcp.bridge import register_mcp_tools
from app.mcp.registry import register_tools
from app.mcp.server import get_mcp_server

_is_bootstrapped = False


def bootstrap_mcp_server() -> FastMCP:
    """
    Register all MCP tools (once) and return the shared server instance.

    Safe to call multiple times -- registration only happens on the
    first call, so importing ``app.main`` and ``app.cli`` in the same
    process (e.g. in tests) never double-registers tools.
    """

    global _is_bootstrapped

    server = get_mcp_server()

    if not _is_bootstrapped:
        register_tools()
        register_mcp_tools()
        _is_bootstrapped = True
        logger.info("mcp_tools_registered")

    return server
