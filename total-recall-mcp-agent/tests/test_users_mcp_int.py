import pytest

from app.mcp.executor import executor
from app.mcp.registry import register_tools


@pytest.mark.asyncio
async def test_get_user_tool():

    register_tools()

    result = await executor.execute(
        "get_user",
        email="test@example.com",
    )

    assert result is not None
    assert result["email"] == "test@example.com"
