"""
MCP Context class:
Contains request-scoped resources available
during tool execution.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class MCPContext:
    """
    Request-scoped MCP execution context.

    This object is created for each MCP request/tool execution.
    """

    principal_id: str
    db_session: AsyncSession | None = None
    request_id: str = field(default_factory=lambda: str(uuid4()))
    user_email: str | None = None
    user_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Add contextual metadata.
        """
        self.metadata[key] = value
