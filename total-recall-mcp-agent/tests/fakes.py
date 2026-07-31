"""
In-memory test doubles for repositories and MCP session wiring.

These keep unit tests fast and free of a running CockroachDB instance.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock
from uuid import UUID

from app.database.models.memory import Memory
from app.database.models.user import User
from app.identity.principal import DEFAULT_PRINCIPAL_ID
from app.mcp.context import MCPContext
from app.mcp.executor import MCPToolExecutor


class FakeMemoryRepository:
    """Stores memories in process for MemoryService unit tests."""

    def __init__(self) -> None:
        self._rows: list[Memory] = []

    async def create(
        self,
        *,
        principal_id: str,
        kind: str,
        content: str,
        metadata: dict | None,
        embedding: list[float],
    ) -> Memory:
        memory = Memory(
            principal_id=principal_id,
            kind=kind,
            content=content,
            metadata_=metadata,
            embedding=embedding,
        )
        self._rows.append(memory)
        return memory

    async def list_by_principal(
        self,
        *,
        principal_id: str,
        kind: str | None = None,
        limit: int = 20,
    ) -> list[Memory]:
        rows = [row for row in self._rows if row.principal_id == principal_id]
        if kind is not None:
            rows = [row for row in rows if row.kind == kind]
        return rows[:limit]

    async def delete_scoped(
        self,
        *,
        principal_id: str,
        memory_id: UUID,
    ) -> bool:
        for index, row in enumerate(self._rows):
            if row.id == memory_id and row.principal_id == principal_id:
                del self._rows[index]
                return True
        return False

    async def search_similar(
        self,
        *,
        principal_id: str,
        query_embedding: list[float],
        kind: str | None = None,
        limit: int = 5,
    ) -> list[tuple[Memory, float]]:
        del query_embedding  # fake search ignores vectors; service tests cover wiring only
        rows = await self.list_by_principal(
            principal_id=principal_id,
            kind=kind,
            limit=limit,
        )
        return [(row, 0.0) for row in rows]


class FakeUserRepository:
    """Returns pre-seeded users keyed by principal_id."""

    def __init__(self, users_by_principal: dict[str, User]) -> None:
        self._users_by_principal = users_by_principal

    async def get_by_principal_id(self, principal_id: str) -> User | None:
        return self._users_by_principal.get(principal_id)


def make_test_user(
    *,
    email: str = "test@example.com",
    first_name: str = "Test",
    last_name: str = "User",
    principal_id: str = DEFAULT_PRINCIPAL_ID,
) -> User:
    return User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        principal_id=principal_id,
        is_active=True,
    )


@asynccontextmanager
async def fake_mcp_session_context() -> AsyncGenerator[MCPContext]:
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    yield MCPContext(
        db_session=session,
        request_id="test-request-id",
        principal_id=DEFAULT_PRINCIPAL_ID,
    )


def apply_mcp_executor_no_db_patches(monkeypatch) -> None:
    """Route MCP tool execution through an in-memory session and skip audit I/O."""

    monkeypatch.setattr(
        "app.mcp.executor.mcp_session_context",
        fake_mcp_session_context,
    )
    monkeypatch.setattr(MCPToolExecutor, "_write_audit", AsyncMock())
