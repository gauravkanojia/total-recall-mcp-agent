"""
Memory repository.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.memory import Memory


class MemoryRepository:
    """
    Repository for semantic memory persistence and vector search.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        principal_id: str,
        kind: str,
        content: str,
        metadata: dict | None,
        embedding: list[float],
    ) -> Memory:
        """
        Persist a new memory row.
        """

        memory = Memory(
            principal_id=principal_id,
            kind=kind,
            content=content,
            metadata_=metadata,
            embedding=embedding,
        )

        self._session.add(memory)
        await self._session.flush()
        await self._session.refresh(memory)

        return memory

    async def list_by_principal(
        self,
        *,
        principal_id: str,
        kind: str | None = None,
        limit: int = 20,
    ) -> list[Memory]:
        """
        Return the caller's memories, newest first.
        """

        statement = (
            select(Memory)
            .where(Memory.principal_id == principal_id)
            .order_by(Memory.created_at.desc())
            .limit(limit)
        )

        if kind is not None:
            statement = statement.where(Memory.kind == kind)

        result = await self._session.execute(statement)

        return list(result.scalars().all())

    async def delete_scoped(
        self,
        *,
        principal_id: str,
        memory_id: UUID,
    ) -> bool:
        """
        Delete one memory, only if it belongs to the caller.

        Scoping by principal_id in the lookup means a caller can never
        delete (or probe the existence of) another principal's memories.
        """

        statement = select(Memory).where(
            Memory.id == memory_id,
            Memory.principal_id == principal_id,
        )

        result = await self._session.execute(statement)
        memory = result.scalar_one_or_none()

        if memory is None:
            return False

        await self._session.delete(memory)
        await self._session.flush()

        return True

    async def search_similar(
        self,
        *,
        principal_id: str,
        query_embedding: list[float],
        kind: str | None = None,
        limit: int = 5,
    ) -> list[tuple[Memory, float]]:
        """
        Return memories ordered by cosine distance to the query embedding.
        """

        distance = Memory.embedding.cosine_distance(query_embedding).label("distance")

        statement = (
            select(Memory, distance)
            .where(Memory.principal_id == principal_id)
            .order_by(distance)
            .limit(limit)
        )

        if kind is not None:
            statement = statement.where(Memory.kind == kind)

        result = await self._session.execute(statement)
        rows = result.all()

        return [(memory, float(distance_value)) for memory, distance_value in rows]
