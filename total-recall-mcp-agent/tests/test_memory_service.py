import pytest

from app.clients.embeddings import FakeEmbeddingProvider
from app.services.memory_service import MemoryService, require_principal_id


@pytest.mark.asyncio
async def test_memory_service_rejects_missing_principal_id():
    provider = FakeEmbeddingProvider(dimensions=1024)
    service = MemoryService(session=None, embedding_provider=provider)

    with pytest.raises(ValueError, match="principal_id is required"):
        await service.remember(
            principal_id=None,
            kind="preference",
            content="User likes dark mode",
        )


def test_require_principal_id_rejects_empty_values():
    with pytest.raises(ValueError, match="principal_id is required"):
        require_principal_id(None)

    with pytest.raises(ValueError, match="principal_id is required"):
        require_principal_id("")


@pytest.mark.asyncio
async def test_memory_service_remember_and_recall(fake_memory_repository):
    provider = FakeEmbeddingProvider(dimensions=1024)
    service = MemoryService(session=None, embedding_provider=provider)
    service.repository = fake_memory_repository

    remembered = await service.remember(
        principal_id="local-test-user",
        kind="preference",
        content="User likes dark mode",
    )

    recalled = await service.recall(
        principal_id="local-test-user",
        query="theme preference",
        kind="preference",
    )

    assert remembered["content"] == "User likes dark mode"
    assert recalled
    assert any("dark mode" in item["content"] for item in recalled)
