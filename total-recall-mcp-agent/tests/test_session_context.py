import pytest

from app.mcp.session_context import mcp_session_context


@pytest.mark.asyncio
async def test_context_creation():

    async with mcp_session_context() as context:
        assert context is not None
        assert context.db_session is not None
        assert context.request_id is not None
        assert context.principal_id == "local-test-user"
