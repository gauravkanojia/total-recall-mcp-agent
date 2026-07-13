import pytest

from app.mcp.middleware import mcp_context_manager


@pytest.mark.asyncio
async def test_context_creation():

    async with mcp_context_manager() as context:
        assert context is not None
        assert context.db_session is not None
        assert context.request_id is not None

    async with mcp_context_manager(token="fake-token") as context:
        assert context.cognito_sub == "local-test-user"
