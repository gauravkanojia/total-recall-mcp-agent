import pytest

from app.mcp.executor import executor
from app.mcp.registry import register_tools


@pytest.mark.asyncio
async def test_remember_and_recall_memory_tools():
    """
    MCP-level integration test for semantic memory tools.
    """

    register_tools()

    remembered = await executor.execute(
        "remember_memory",
        content="User likes dark mode",
        kind="preference",
    )

    recalled = await executor.execute(
        "recall_memory",
        query="theme preference",
        kind="preference",
    )

    assert remembered["content"] == "User likes dark mode"
    assert any("dark mode" in item["content"] for item in recalled)
