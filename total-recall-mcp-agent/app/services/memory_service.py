"""
Memory business logic.
"""

from app.clients.embeddings import EmbeddingProvider
from app.repositories.memory_repository import MemoryRepository


class MemoryService:
    """
    Service for remembering and recalling semantic agent memory.
    """

    def __init__(self, session, embedding_provider: EmbeddingProvider) -> None:
        self.repository = MemoryRepository(session)
        self.embedding_provider = embedding_provider

    async def remember(
        self,
        *,
        cognito_sub: str | None,
        kind: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        """
        Embed and persist a memory.
        """

        embedding = await self.embedding_provider.embed(content)

        memory = await self.repository.create(
            cognito_sub=cognito_sub,
            kind=kind,
            content=content,
            metadata=metadata,
            embedding=embedding,
        )

        return {
            "id": str(memory.id),
            "kind": memory.kind,
            "content": memory.content,
        }

    async def recall(
        self,
        *,
        cognito_sub: str | None,
        query: str,
        kind: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """
        Embed a query and return the closest memories.
        """

        query_embedding = await self.embedding_provider.embed(query)

        rows = await self.repository.search_similar(
            cognito_sub=cognito_sub,
            query_embedding=query_embedding,
            kind=kind,
            limit=limit,
        )

        return [
            {
                "id": str(memory.id),
                "kind": memory.kind,
                "content": memory.content,
                "distance": distance,
            }
            for memory, distance in rows
        ]
