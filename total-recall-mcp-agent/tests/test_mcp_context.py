from app.mcp.context import MCPContext
from app.mcp.context_manager import get_context


def test_mcp_context_creation():
    """
    beta
    """
    context = MCPContext()

    assert context.request_id is not None
    assert context.created_at is not None
    assert context.user_id is None


def test_mcp_context_metadata():
    """
    test_mcp_context
    """
    context = MCPContext(
        request_id="test-request",
        user_email="test@example.com",
    )
    context.add_metadata(
        "source",
        "test",
    )

    current = get_context()

    assert current is not None
    assert current.request_id == "test-request"
    assert current.user_email == "test@example.com"
    assert context.metadata["source"] == "test"
    # assert token is True
