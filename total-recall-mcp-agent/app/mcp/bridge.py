"""
FastMCP bridge.

Connects FastMCP exposed tools
to internal executor tools.
"""

from app.core.logging import logger
from app.mcp.executor import executor
from app.mcp.server import get_mcp_server


async def _execute_tool(name: str, **kwargs):
    """
    Run an internal tool handler, sanitizing unexpected errors.

    Validation errors (ValueError) carry safe, intentional messages and pass
    through to the client. Anything else (DB errors, provider failures) is
    logged and audited server-side, and the client sees a generic message —
    never SQL fragments, hostnames, or stack details.
    """

    try:
        return await executor.execute(name, **kwargs)
    except ValueError:
        raise
    except Exception:
        logger.exception("tool_execution_failed", tool_name=name)
        raise RuntimeError(
            f"Internal error while executing '{name}'. "
            "Details are in server logs and the audit_logs table."
        ) from None


def register_mcp_tools() -> None:
    """
    Register public MCP tools.
    """

    mcp_server = get_mcp_server()

    @mcp_server.tool()
    async def health_check() -> dict:
        return await _execute_tool("health_check")

    @mcp_server.tool()
    async def get_user() -> dict | None:
        """Return the authenticated caller's user record, if one exists."""

        return await _execute_tool("get_user")

    @mcp_server.tool()
    async def remember_memory(
        content: str,
        kind: str = "fact",
        metadata: dict | None = None,
    ) -> dict:
        return await _execute_tool(
            "remember_memory",
            content=content,
            kind=kind,
            metadata=metadata,
        )

    @mcp_server.tool()
    async def recall_memory(
        query: str,
        kind: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        return await _execute_tool(
            "recall_memory",
            query=query,
            kind=kind,
            limit=limit,
        )

    @mcp_server.tool()
    async def list_memories(
        kind: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """List the caller's stored memories, newest first."""

        return await _execute_tool(
            "list_memories",
            kind=kind,
            limit=limit,
        )

    @mcp_server.tool()
    async def forget_memory(
        memory_id: str,
    ) -> dict:
        """Delete one of the caller's memories by id (audited)."""

        return await _execute_tool(
            "forget_memory",
            memory_id=memory_id,
        )
