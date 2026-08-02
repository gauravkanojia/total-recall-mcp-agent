"""
Seed sample semantic memories for demos and local testing.
"""

import asyncio

from app.clients.embeddings import FakeEmbeddingProvider
from app.core.config import settings
from app.database.session import get_session_factory
from app.services.memory_service import MemoryService

SAMPLE_MEMORIES = [
    {
        "kind": "preference",
        "content": "User prefers dark mode in all applications.",
        "metadata": {"source": "onboarding"},
    },
    {
        "kind": "fact",
        "content": "The user's primary database is CockroachDB on AWS.",
        "metadata": {"source": "onboarding"},
    },
    {
        "kind": "task_state",
        "content": "Current task: finish hackathon submission for Total Recall MCP agent.",
        "metadata": {"session_id": "demo-session"},
    },
]


async def seed_memories() -> None:
    session_factory = get_session_factory()
    provider = FakeEmbeddingProvider(dimensions=settings.EMBEDDING_DIMENSIONS)

    async with session_factory() as session:
        service = MemoryService(session, provider)

        for item in SAMPLE_MEMORIES:
            remembered = await service.remember(
                principal_id="local-test-user",
                kind=item["kind"],
                content=item["content"],
                metadata=item["metadata"],
            )
            print(f"Seeded memory: {remembered['kind']} -> {remembered['content']}")

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_memories())
