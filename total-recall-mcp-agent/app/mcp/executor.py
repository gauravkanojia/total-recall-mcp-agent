"""
MCP tool execution abstraction.
"""

from collections.abc import Callable
from typing import Any

from app.mcp.middleware import mcp_context_manager
from app.repositories.audit_repository import AuditRepository


class MCPToolExecutor:
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
        self._tools.clear()

    async def execute(
        self,
        name: str,
        *,
        token=None,
        **kwargs,
    ) -> Any:

        if name not in self._tools:
            raise ValueError(f"Unknown MCP tool: {name}")

        handler = self._tools[name]

        async with mcp_context_manager(token=token) as context:
            audit = AuditRepository(context.db_session)

            await audit.create(
                tool_name=name,
                request_id=context.request_id,
                cognito_sub=context.cognito_sub,
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
                    cognito_sub=context.cognito_sub,
                    status="FAILED",
                    error_message=str(exc),
                )

                await context.db_session.rollback()
                raise


executor = MCPToolExecutor()
