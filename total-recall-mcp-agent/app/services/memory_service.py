"""
Memory business logic.
"""

from app.clients.embeddings import EmbeddingProvider
from app.repositories.memory_repository import MemoryRepository


def require_principal_id(principal_id: str | None) -> str:
    """
    Reject memory operations without a caller principal.
    """

    if not principal_id:
        raise ValueError("principal_id is required for memory operations")

    return principal_id


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
        principal_id: str | None,
        kind: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        """
        Embed and persist a memory.
        """

        scope_id = require_principal_id(principal_id)
        embedding = await self.embedding_provider.embed(content)

        memory = await self.repository.create(
            principal_id=scope_id,
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
        principal_id: str | None,
        query: str,
        kind: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """
        Embed a query and return the closest memories.
        """

        scope_id = require_principal_id(principal_id)
        query_embedding = await self.embedding_provider.embed(query)

        rows = await self.repository.search_similar(
            principal_id=scope_id,
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
