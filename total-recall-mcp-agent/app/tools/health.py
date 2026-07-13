"""
Health MCP tools.
"""

from app.mcp.executor import executor


async def health_check(
    context=None,
) -> dict:
    """
    Internal health handler.
    """

    return {
        "status": "healthy",
        "service": "total-recall-mcp-agent",
    }


def register_health_tools() -> None:
    """
    Register health tools.
    """

    executor.register(
        "health_check",
        health_check,
    )
