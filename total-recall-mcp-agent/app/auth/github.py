"""
GitHub-backed bearer-token validation for HTTP transports.

Callers send `Authorization: Bearer <github-token>` (a PAT or OAuth token).
The token is validated against the GitHub API and mapped to a stable
principal (`github:<login>`). Static tokens from MCP_STATIC_TOKENS are
checked first so demos keep working even if GitHub is unreachable.
"""

import hashlib
from http import HTTPStatus
import time

import httpx

from app.core.config import get_settings
from app.core.logging import logger
from app.identity.principal import MCPPrincipal

GITHUB_API_TIMEOUT_SECONDS = 5.0


class GitHubTokenValidator:
    """Validate bearer tokens with a TTL cache over the GitHub API."""

    def __init__(self) -> None:
        settings = get_settings()

        self._mode = settings.HTTP_AUTH_MODE
        self._api_url = settings.GITHUB_API_URL.rstrip("/")
        self._ttl_seconds = settings.AUTH_CACHE_TTL_SECONDS
        self._cache: dict[str, tuple[float, MCPPrincipal]] = {}
        self._static_tokens = self._parse_static_tokens(settings.MCP_STATIC_TOKENS)

    @staticmethod
    def _parse_static_tokens(raw: str) -> dict[str, MCPPrincipal]:
        """Parse MCP_STATIC_TOKENS ("token:principal-id,token2:other") pairs."""

        tokens: dict[str, MCPPrincipal] = {}

        for pair in raw.split(","):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue
            token, principal_id = pair.split(":", 1)
            if token.strip() and principal_id.strip():
                tokens[token.strip()] = MCPPrincipal(principal_id=principal_id.strip())

        return tokens

    async def validate(self, token: str) -> MCPPrincipal | None:
        """Return the principal for a bearer token, or None if invalid."""

        static_principal = self._static_tokens.get(token)
        if static_principal is not None:
            return static_principal

        if self._mode == "static":
            return None

        cache_key = hashlib.sha256(token.encode()).hexdigest()
        cached = self._cache.get(cache_key)
        now = time.monotonic()

        if cached is not None and cached[0] > now:
            return cached[1]

        principal = await self._fetch_github_user(token)

        if principal is not None:
            self._cache[cache_key] = (now + self._ttl_seconds, principal)

        return principal

    async def _fetch_github_user(self, token: str) -> MCPPrincipal | None:
        """Resolve a GitHub token to its user via GET /user."""

        try:
            async with httpx.AsyncClient(timeout=GITHUB_API_TIMEOUT_SECONDS) as client:
                response = await client.get(
                    f"{self._api_url}/user",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                )
        except httpx.HTTPError as exc:
            logger.warning("github_auth_unreachable", error=str(exc))
            return None

        if response.status_code != HTTPStatus.OK:
            logger.info("github_auth_rejected", status_code=response.status_code)
            return None

        payload = response.json()
        login = payload.get("login")

        if not login:
            return None

        return MCPPrincipal(
            principal_id=f"github:{login}",
            email=payload.get("email"),
        )
