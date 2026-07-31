"""
Integration tests against a live CockroachDB instance.

Skipped automatically when DATABASE_URL is not reachable; run explicitly with:

    uv run pytest -m integration
"""

import pytest

from app.clients.embeddings import FakeEmbeddingProvider
from app.database.session import get_session_factory
from app.identity.principal import DEFAULT_PRINCIPAL_ID
from app.mcp.executor import executor
from app.mcp.registry import register_tools
from app.services.memory_service import MemoryService

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_memory_service_remember_and_recall_against_database():
    session_factory = get_session_factory()
    provider = FakeEmbeddingProvider(dimensions=1024)

    async with session_factory() as session:
        service = MemoryService(session, provider)

        remembered = await service.remember(
            principal_id=DEFAULT_PRINCIPAL_ID,
            kind="preference",
            content="User likes dark mode",
        )

        recalled = await service.recall(
            principal_id=DEFAULT_PRINCIPAL_ID,
            query="theme preference",
            kind="preference",
        )

        await session.commit()

    assert remembered["content"] == "User likes dark mode"
    assert recalled
    assert any("dark mode" in item["content"] for item in recalled)


@pytest.mark.asyncio
async def test_remember_and_recall_memory_tools_against_database():
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


@pytest.mark.asyncio
async def test_get_user_tool_returns_caller_record_from_database():
    register_tools()

    result = await executor.execute("get_user")

    assert result is not None
    assert result["principal_id"] == DEFAULT_PRINCIPAL_ID
    assert result["email"] == "test@example.com"
