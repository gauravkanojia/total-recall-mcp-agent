"""
MCP tool execution abstraction.
"""

from collections.abc import Callable
from typing import Any

from app.core.logging import logger
from app.database.session import get_session_factory
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
            await self._write_audit(
                tool_name=name,
                request_id=context.request_id,
                principal_id=context.principal_id,
                status="STARTED",
            )

            try:
                result = await handler(
                    context=context,
                    **kwargs,
                )

                await context.db_session.commit()
            except Exception as exc:
                await context.db_session.rollback()
                await self._write_audit(
                    tool_name=name,
                    request_id=context.request_id,
                    principal_id=context.principal_id,
                    status="FAILED",
                    error_message=str(exc),
                )
                raise

            await self._write_audit(
                tool_name=name,
                request_id=context.request_id,
                principal_id=context.principal_id,
                status="SUCCEEDED",
            )

            return result

    @staticmethod
    async def _write_audit(
        *,
        tool_name: str,
        request_id: str,
        principal_id: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """
        Record an audit row in its own transaction.

        Audit writes are isolated from the tool's DB session so the trail
        survives tool rollbacks: STARTED is durable before the handler runs,
        and FAILED is recorded after the work is rolled back.
        """

        try:
            session_factory = get_session_factory()

            async with session_factory() as session:
                audit = AuditRepository(session)
                await audit.create(
                    tool_name=tool_name,
                    request_id=request_id,
                    principal_id=principal_id,
                    status=status,
                    error_message=error_message,
                )
                await session.commit()
        except Exception as exc:  # noqa: BLE001 — audit must never mask tool results
            logger.error(
                "audit_write_failed",
                tool_name=tool_name,
                request_id=request_id,
                status=status,
                error=str(exc),
            )


executor = MCPToolExecutor()
