import pytest

from app.mcp.executor import executor


@pytest.mark.asyncio
async def test_context_contains_principal():

    async def whoami(context):

        return {"principal_id": context.principal_id}

    executor.register(
        "whoami",
        whoami,
    )

    result = await executor.execute("whoami")

    assert result["principal_id"] == "local-test-user"
