import pytest

from app.mcp.executor import executor
from app.tools.health import register_health_tools


@pytest.mark.asyncio
async def test_health_tool_execution():

    register_health_tools()

    result = await executor.execute("health_check")

    assert result["status"] == "healthy"
