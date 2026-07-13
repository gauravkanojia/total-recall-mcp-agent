"""
MCP tool registry.

All MCP tools are registered here.
"""

from app.tools.health import register_health_tools
from app.tools.memory import register_memory_tools
from app.tools.users import register_user_tools


def register_tools() -> None:
    """
    Register all MCP tools.
    """

    register_health_tools()
    register_user_tools()
    register_memory_tools()
