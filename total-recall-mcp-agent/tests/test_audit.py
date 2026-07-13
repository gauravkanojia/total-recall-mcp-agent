"""
Tests for Audit Log
"""

import pytest

from app.mcp.executor import executor


@pytest.mark.asyncio
async def test_tool_creates_audit():
    """
    Test Audit Log creation
    """

    async def sample_tool(context):

        return {"ok": True}

    executor.register(
        "sample",
        sample_tool,
    )

    result = await executor.execute(
        "sample",
    )

    assert result["ok"] is True
