"""
Default MCP caller identity for per-user memory scoping.
"""

from dataclasses import dataclass

DEFAULT_PRINCIPAL_ID = "local-test-user"
DEFAULT_PRINCIPAL_EMAIL = "test@example.com"


@dataclass
class MCPPrincipal:
    """Caller identity attached to each MCP tool execution."""

    principal_id: str
    email: str | None = None


def resolve_mcp_principal() -> MCPPrincipal:
    """Return the default MCP caller used for memory and audit scoping."""

    return MCPPrincipal(
        principal_id=DEFAULT_PRINCIPAL_ID,
        email=DEFAULT_PRINCIPAL_EMAIL,
    )
