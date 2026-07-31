"""
MCP caller identity for per-user memory scoping.

HTTP transports authenticate callers (see app/auth) and bind the resulting
principal to `current_principal` for the duration of the request. stdio
transport (local dev in Cursor / Claude Desktop) falls back to the default
local principal.
"""

from contextvars import ContextVar
from dataclasses import dataclass

DEFAULT_PRINCIPAL_ID = "local-test-user"
DEFAULT_PRINCIPAL_EMAIL = "test@example.com"


@dataclass
class MCPPrincipal:
    """Caller identity attached to each MCP tool execution."""

    principal_id: str
    email: str | None = None


current_principal: ContextVar[MCPPrincipal | None] = ContextVar(
    "current_principal",
    default=None,
)


def resolve_mcp_principal() -> MCPPrincipal:
    """
    Return the caller identity for the current tool execution.

    Auth middleware sets `current_principal` per authenticated HTTP request;
    stdio and auth-off modes fall back to the local development principal.
    """

    principal = current_principal.get()
    if principal is not None:
        return principal

    return MCPPrincipal(
        principal_id=DEFAULT_PRINCIPAL_ID,
        email=DEFAULT_PRINCIPAL_EMAIL,
    )
