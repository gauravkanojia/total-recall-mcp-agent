"""
Tests for GitHub-backed bearer auth and principal resolution.
"""

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.auth.github import GitHubTokenValidator
from app.auth.middleware import BearerAuthMiddleware
from app.core.config import get_settings
from app.identity.principal import (
    DEFAULT_PRINCIPAL_ID,
    MCPPrincipal,
    current_principal,
    resolve_mcp_principal,
)


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """New Settings per test so env overrides apply."""

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _build_app() -> Starlette:
    async def whoami(_request):
        return JSONResponse({"principal": resolve_mcp_principal().principal_id})

    async def health(_request):
        return JSONResponse({"status": "ok"})

    app = Starlette(
        routes=[
            Route("/whoami", whoami),
            Route("/health", health),
        ]
    )
    app.add_middleware(BearerAuthMiddleware)
    return app


# --- principal resolution -------------------------------------------------


def test_resolve_falls_back_to_default_principal():
    assert resolve_mcp_principal().principal_id == DEFAULT_PRINCIPAL_ID


def test_resolve_uses_bound_principal():
    token = current_principal.set(MCPPrincipal(principal_id="github:alice"))
    try:
        assert resolve_mcp_principal().principal_id == "github:alice"
    finally:
        current_principal.reset(token)


# --- static token validation ----------------------------------------------


@pytest.mark.asyncio
async def test_static_tokens_map_to_principals(monkeypatch):
    monkeypatch.setenv("HTTP_AUTH_MODE", "static")
    monkeypatch.setenv("MCP_STATIC_TOKENS", "tok-a:alice, tok-b:bob")
    get_settings.cache_clear()

    validator = GitHubTokenValidator()

    alice = await validator.validate("tok-a")
    bob = await validator.validate("tok-b")

    assert alice is not None and alice.principal_id == "alice"
    assert bob is not None and bob.principal_id == "bob"
    assert await validator.validate("unknown") is None


@pytest.mark.asyncio
async def test_github_mode_uses_api_result(monkeypatch):
    monkeypatch.setenv("HTTP_AUTH_MODE", "github")
    get_settings.cache_clear()

    validator = GitHubTokenValidator()

    async def fake_fetch(_token):
        return MCPPrincipal(principal_id="github:gauravkanojia")

    monkeypatch.setattr(validator, "_fetch_github_user", fake_fetch)

    principal = await validator.validate("gho_sometoken")

    assert principal is not None
    assert principal.principal_id == "github:gauravkanojia"

    # Second call is served from cache (fetch would fail loudly if called).
    async def exploding_fetch(_token):
        raise AssertionError("cache miss")

    monkeypatch.setattr(validator, "_fetch_github_user", exploding_fetch)
    cached = await validator.validate("gho_sometoken")

    assert cached is not None and cached.principal_id == "github:gauravkanojia"


# --- middleware -----------------------------------------------------------


def test_middleware_off_mode_passes_through(monkeypatch):
    monkeypatch.setenv("HTTP_AUTH_MODE", "off")
    get_settings.cache_clear()

    client = TestClient(_build_app())
    response = client.get("/whoami")

    assert response.status_code == 200
    assert response.json()["principal"] == DEFAULT_PRINCIPAL_ID


def test_middleware_rejects_missing_token(monkeypatch):
    monkeypatch.setenv("HTTP_AUTH_MODE", "static")
    monkeypatch.setenv("MCP_STATIC_TOKENS", "tok-a:alice")
    get_settings.cache_clear()

    client = TestClient(_build_app())

    assert client.get("/whoami").status_code == 401
    assert client.get("/whoami", headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_middleware_binds_principal_and_allows_health(monkeypatch):
    monkeypatch.setenv("HTTP_AUTH_MODE", "static")
    monkeypatch.setenv("MCP_STATIC_TOKENS", "tok-a:alice")
    get_settings.cache_clear()

    client = TestClient(_build_app())

    authed = client.get("/whoami", headers={"Authorization": "Bearer tok-a"})
    assert authed.status_code == 200
    assert authed.json()["principal"] == "alice"

    # /health stays public for the ALB.
    assert client.get("/health").status_code == 200
