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
        cognito_sub=context.cognito_sub,
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

    return await service.recall(
        cognito_sub=context.cognito_sub,
        query=query,
        kind=kind,
        limit=limit,
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
