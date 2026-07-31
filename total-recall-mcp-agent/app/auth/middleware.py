"""
Bearer-token authentication middleware for MCP HTTP transports.

Every request (except public paths like /health) must present
`Authorization: Bearer <token>`. Valid callers get a request-scoped
principal bound for per-user memory isolation; everything else is 401.
Auth is skipped entirely when HTTP_AUTH_MODE=off (local development).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.auth.github import GitHubTokenValidator
from app.core.config import get_settings
from app.identity.principal import current_principal

PUBLIC_PATHS = {"/health", "/ready"}


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Authenticate HTTP MCP calls and bind the caller principal."""

    def __init__(self, app) -> None:
        super().__init__(app)
        self._validator = GitHubTokenValidator()

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()

        if settings.HTTP_AUTH_MODE == "off" or request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")

        if not auth_header.lower().startswith("bearer "):
            return JSONResponse(
                {"error": "missing_bearer_token"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header[7:].strip()
        principal = await self._validator.validate(token)

        if principal is None:
            return JSONResponse(
                {"error": "invalid_token"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )

        reset_token = current_principal.set(principal)
        try:
            return await call_next(request)
        finally:
            current_principal.reset(reset_token)
