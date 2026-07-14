"""MCP caller identity (memory scope), not authentication."""

from app.identity.principal import (
    DEFAULT_PRINCIPAL_EMAIL,
    DEFAULT_PRINCIPAL_ID,
    MCPPrincipal,
    resolve_mcp_principal,
)

__all__ = [
    "DEFAULT_PRINCIPAL_EMAIL",
    "DEFAULT_PRINCIPAL_ID",
    "MCPPrincipal",
    "resolve_mcp_principal",
]
