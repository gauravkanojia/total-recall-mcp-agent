from app.mcp.bridge import register_mcp_tools
from app.mcp.registry import register_tools
from app.mcp.server import get_mcp_server


def test_mcp_bridge():

    register_tools()
    register_mcp_tools()

    server = get_mcp_server()

    assert server.name == "total-recall-mcp-agent"
