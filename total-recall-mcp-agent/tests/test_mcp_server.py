"""
Test bootstrapping for MCP Server
"""

from app.mcp.server import get_mcp_server
from app.mcp.registry import register_tools


def test_mcp_server_creation():
    """
    Test creation of MCP Server
    """
    server = get_mcp_server()
    register_tools()

    assert server is not None
    assert server.name == "total-recall-mcp-agent"
