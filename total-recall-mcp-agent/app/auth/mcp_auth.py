"""
MCP authentication helpers.
"""

from dataclasses import dataclass


@dataclass
class MCPPrincipal:
    """
    Authenticated MCP caller.
    """

    cognito_sub: str

    email: str | None = None


def validate_mcp_token(
    token: str,
) -> MCPPrincipal:
    """
    Validate incoming MCP token.

    Placeholder for Cognito JWT validation.
    """

    # Real implementation will:
    #
    # 1. Decode JWT header
    # 2. Fetch Cognito JWKS
    # 3. Validate signature
    # 4. Validate issuer/audience
    #

    return MCPPrincipal(
        cognito_sub="local-test-user",
        email="test@example.com",
    )
