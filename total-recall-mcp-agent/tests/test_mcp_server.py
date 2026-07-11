from app.mcp.server import create_mcp_server


def test_mcp_server_creation():

    server = create_mcp_server()
    assert server is not None
