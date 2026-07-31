"""
Memory business logic.
"""

import json
from uuid import UUID

from app.clients.embeddings import EmbeddingProvider
from app.repositories.memory_repository import MemoryRepository

# Input bounds: fail fast with clear messages instead of surfacing DB
# constraint or Bedrock errors to MCP clients.
MAX_CONTENT_CHARS = 8_000  # comfortably inside Titan v2 input limits
MAX_KIND_CHARS = 50  # matches memories.kind STRING(50)
MAX_METADATA_BYTES = 16_384
MAX_RECALL_LIMIT = 50


def require_principal_id(principal_id: str | None) -> str:
    """
    Reject memory operations without a caller principal.
    """

    if not principal_id:
        raise ValueError("principal_id is required for memory operations")

    return principal_id


def validate_content(content: str) -> str:
    """
    Require non-empty content within the embedding provider's limits.
    """

    if not content or not content.strip():
        raise ValueError("content must not be empty")

    if len(content) > MAX_CONTENT_CHARS:
        raise ValueError(f"content exceeds {MAX_CONTENT_CHARS} characters")

    return content


def validate_kind(kind: str) -> str:
    """
    Require a kind that fits the memories.kind column.
    """

    if not kind or not kind.strip():
        raise ValueError("kind must not be empty")

    if len(kind) > MAX_KIND_CHARS:
        raise ValueError(f"kind exceeds {MAX_KIND_CHARS} characters")

    return kind


def validate_metadata(metadata: dict | None) -> dict | None:
    """
    Bound the serialized size of memory metadata.
    """

    if metadata is None:
        return None

    if len(json.dumps(metadata)) > MAX_METADATA_BYTES:
        raise ValueError(f"metadata exceeds {MAX_METADATA_BYTES} bytes serialized")

    return metadata


def validate_limit(limit: int) -> int:
    """
    Bound recall result counts.
    """

    if not 1 <= limit <= MAX_RECALL_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_RECALL_LIMIT}")

    return limit


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
        content = validate_content(content)
        kind = validate_kind(kind)
        metadata = validate_metadata(metadata)

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
        query = validate_content(query)
        limit = validate_limit(limit)
        if kind is not None:
            kind = validate_kind(kind)

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

    async def list_memories(
        self,
        *,
        principal_id: str | None,
        kind: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """
        Return the caller's memories, newest first (no embedding involved).
        """

        scope_id = require_principal_id(principal_id)
        limit = validate_limit(limit)
        if kind is not None:
            kind = validate_kind(kind)

        memories = await self.repository.list_by_principal(
            principal_id=scope_id,
            kind=kind,
            limit=limit,
        )

        return [
            {
                "id": str(memory.id),
                "kind": memory.kind,
                "content": memory.content,
                "metadata": memory.metadata_,
                "created_at": memory.created_at.isoformat(),
            }
            for memory in memories
        ]

    async def forget(
        self,
        *,
        principal_id: str | None,
        memory_id: str,
    ) -> dict:
        """
        Delete one of the caller's memories (audited like every tool call).
        """

        scope_id = require_principal_id(principal_id)

        try:
            parsed_id = UUID(memory_id)
        except (ValueError, AttributeError, TypeError) as exc:
            raise ValueError("memory_id must be a valid UUID") from exc

        deleted = await self.repository.delete_scoped(
            principal_id=scope_id,
            memory_id=parsed_id,
        )

        return {
            "id": memory_id,
            "deleted": deleted,
        }
