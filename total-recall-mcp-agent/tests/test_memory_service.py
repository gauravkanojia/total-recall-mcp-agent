import pytest

from app.clients.embeddings import FakeEmbeddingProvider
from app.database.session import get_session_factory
from app.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_memory_service_remember_and_recall():
    """
    Remember a memory and recall it with a related query.
    """

    session_factory = get_session_factory()
    provider = FakeEmbeddingProvider(dimensions=1024)

    async with session_factory() as session:
        service = MemoryService(session, provider)

        remembered = await service.remember(
            cognito_sub="local-test-user",
            kind="preference",
            content="User likes dark mode",
        )

        recalled = await service.recall(
            cognito_sub="local-test-user",
            query="theme preference",
            kind="preference",
        )

        await session.commit()

    assert remembered["content"] == "User likes dark mode"
    assert recalled
    assert any("dark mode" in item["content"] for item in recalled)
