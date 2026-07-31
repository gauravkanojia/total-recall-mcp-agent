"""
Application bootstrap.

The stdio and streamable-HTTP entry points (``app.cli``) share one bootstrap
path so MCP tools are registered in a single place and never drift out of sync.
"""

from mcp.server.fastmcp import FastMCP

from app.core.logging import logger
from app.mcp.bridge import register_mcp_tools
from app.mcp.registry import register_tools
from app.mcp.server import get_mcp_server

_is_bootstrapped = False  # pylint: disable=invalid-name


def bootstrap_mcp_server() -> FastMCP:
    """
    Register all MCP tools (once) and return the shared server instance.

    Safe to call multiple times -- registration only happens on the
    first call, so repeated imports in the same process (e.g. in tests)
    never double-registers tools.
    """

    global _is_bootstrapped  # pylint: disable=global-statement

    server = get_mcp_server()

    if not _is_bootstrapped:
        register_tools()
        register_mcp_tools()
        _is_bootstrapped = True
        logger.info("mcp_tools_registered")

    return server
