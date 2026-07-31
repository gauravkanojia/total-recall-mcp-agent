"""
Authentication for MCP HTTP transports.

GitHub-backed bearer tokens (with static-token fallback) map callers to
principals for per-user memory isolation. stdio transport is unauthenticated
by design (local, single-user).
"""

from app.auth.github import GitHubTokenValidator
from app.auth.middleware import BearerAuthMiddleware

__all__ = [
    "BearerAuthMiddleware",
    "GitHubTokenValidator",
]
