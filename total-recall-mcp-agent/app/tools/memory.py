"""
Memory MCP tools.
"""

from app.clients.embeddings import get_embedding_provider
from app.mcp.executor import executor
from app.services.memory_service import MemoryService


async def remember_memory(
    content: str,
    kind: str = "fact",
    metadata: dict | None = None,
    context=None,
):
    """
    Store a semantic memory for later recall.
    """

    provider = get_embedding_provider()
    service = MemoryService(context.db_session, provider)

    return await service.remember(
        principal_id=context.principal_id,
        kind=kind,
        content=content,
        metadata=metadata,
    )


async def recall_memory(
    query: str,
    kind: str | None = None,
    limit: int = 5,
    context=None,
):
    """
    Recall memories similar to the provided query.
    """

    provider = get_embedding_provider()
    service = MemoryService(context.db_session, provider)

    # Note: recall results are intentionally NOT logged — memory content is
    # user data and must not end up in stderr/CloudWatch.
    return await service.recall(
        principal_id=context.principal_id,
        query=query,
        kind=kind,
        limit=limit,
    )


async def list_memories(
    kind: str | None = None,
    limit: int = 20,
    context=None,
):
    """
    List the caller's stored memories, newest first.
    """

    provider = get_embedding_provider()
    service = MemoryService(context.db_session, provider)

    return await service.list_memories(
        principal_id=context.principal_id,
        kind=kind,
        limit=limit,
    )


async def forget_memory(
    memory_id: str,
    context=None,
):
    """
    Delete one of the caller's memories by id.
    """

    provider = get_embedding_provider()
    service = MemoryService(context.db_session, provider)

    return await service.forget(
        principal_id=context.principal_id,
        memory_id=memory_id,
    )


def register_memory_tools() -> None:
    """
    Register memory MCP tools.
    """

    executor.register(
        "remember_memory",
        remember_memory,
    )
    executor.register(
        "recall_memory",
        recall_memory,
    )
    executor.register(
        "list_memories",
        list_memories,
    )
    executor.register(
        "forget_memory",
        forget_memory,
    )
