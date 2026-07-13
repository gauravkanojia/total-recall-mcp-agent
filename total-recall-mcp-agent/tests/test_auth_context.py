import pytest

from app.mcp.executor import executor


@pytest.mark.asyncio
async def test_context_contains_identity():

    async def whoami(context):

        return {"cognito_sub": context.cognito_sub}

    executor.register(
        "whoami",
        whoami,
    )

    result = await executor.execute(
        "whoami",
        token="fake-token",
    )

    assert result["cognito_sub"] == "local-test-user"
