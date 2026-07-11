from app.tools.health import register_health_tools


def test_healthy_mcp_server():
    assert register_health_tools is not None
