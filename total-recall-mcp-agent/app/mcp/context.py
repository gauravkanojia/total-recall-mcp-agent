"""
MCP Context class:
Contains request-scoped resources available
during tool execution.
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4
from datetime import UTC, datetime
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class MCPContext:
    """
    Request-scoped MCP execution context.

    This object is created for each MCP request/tool execution.
    """

    db_session: AsyncSession | None = None
    request_id: UUID = field(default_factory=uuid4)
    user_email: str | None = None
    user_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    cognito_sub: str | None = None
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
