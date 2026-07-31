import pytest

from app.identity.principal import DEFAULT_PRINCIPAL_ID
from app.mcp.executor import executor
from app.mcp.registry import register_tools


@pytest.mark.asyncio
async def test_get_user_tool_returns_caller_record(
    patch_mcp_executor_no_db,
    patch_user_service_repository,
):
    """get_user is scoped to the calling principal (no arbitrary lookup)."""

    register_tools()

    result = await executor.execute("get_user")

    assert result is not None
    assert result["principal_id"] == DEFAULT_PRINCIPAL_ID
    assert result["email"] == "test@example.com"
