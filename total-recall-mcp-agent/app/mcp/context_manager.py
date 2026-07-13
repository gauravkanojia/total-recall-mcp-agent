"""
MCP context lifecycle management.
"""

from contextvars import ContextVar

from app.mcp.context import MCPContext

_current_context: ContextVar[MCPContext | None] = ContextVar(
    "mcp_context",
    default=None,
)


def set_context(context: MCPContext):
    """
    Set current MCP context.
    """

    return _current_context.set(context)


def get_context() -> MCPContext | None:
    """
    Get current MCP context.
    """

    return _current_context.get()


def clear_context(token):
    """
    Clear context.
    """

    _current_context.reset(token)
