from app.mcp.registry import register_tools
from app.mcp.server import get_mcp_server


def test_mcp_server():
    """
    Testing MCP Server bootstrap
    """
    server = get_mcp_server()

    register_tools()

    assert server is not None
    assert server.name == "total-recall-mcp-agent"
