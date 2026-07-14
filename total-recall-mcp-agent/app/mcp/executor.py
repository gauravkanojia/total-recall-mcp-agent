"""
MCP tool execution abstraction.
"""

from collections.abc import Callable
from typing import Any

from app.mcp.session_context import mcp_session_context
from app.repositories.audit_repository import AuditRepository


class MCPToolExecutor:
    """Register and run MCP tool handlers inside an audited DB context."""

    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(
        self,
        name: str,
        handler: Callable,
    ) -> None:
        """
        Register or replace a tool handler.
        """
        self._tools[name] = handler

    def clear(self) -> None:
        """Remove all registered tool handlers."""

        self._tools.clear()

    async def execute(
        self,
        name: str,
        **kwargs,
    ) -> Any:
        """Run a registered tool handler and commit or roll back the DB session."""

        if name not in self._tools:
            raise ValueError(f"Unknown MCP tool: {name}")

        handler = self._tools[name]

        async with mcp_session_context() as context:
            audit = AuditRepository(context.db_session)

            await audit.create(
                tool_name=name,
                request_id=context.request_id,
                principal_id=context.principal_id,
                status="STARTED",
                error_message=None,
            )

            try:
                result = await handler(
                    context=context,
                    **kwargs,
                )

                await context.db_session.commit()
                return result
            except Exception as exc:
                await audit.create(
                    tool_name=name,
                    request_id=context.request_id,
                    principal_id=context.principal_id,
                    status="FAILED",
                    error_message=str(exc),
                )

                await context.db_session.rollback()
                raise


executor = MCPToolExecutor()
