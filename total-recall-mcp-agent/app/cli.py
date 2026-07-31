"""
Standalone entry point for the Total Recall MCP server.

This is what MCP clients (Cursor, Claude Desktop, etc.) launch directly,
typically over stdio:

    uv run total-recall-mcp-agent
    uv run python -m app.cli
    uv run python -m app.cli --transport streamable-http --port 4646
"""

import argparse
import os
import signal

from app.bootstrap import bootstrap_mcp_server
from app.core.config import settings
from app.core.logging import logger, setup_logging


def parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments, falling back to application settings.
    """

    parser = argparse.ArgumentParser(
        prog="total-recall-mcp-agent",
        description="Run the Total Recall MCP agent server.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=settings.MCP_TRANSPORT,
        help="MCP transport to serve (default: %(default)s).",
    )
    parser.add_argument(
        "--host",
        default=settings.HOST,
        help="Bind host for HTTP transports (default: %(default)s).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.PORT,
        help="Bind port for HTTP transports (default: %(default)s).",
    )

    return parser.parse_args()


def _register_shutdown_handlers() -> None:
    """
    Handle SIGINT/SIGTERM without racing MCP stdio thread teardown.

    FastMCP blocks on stdin inside anyio; a default KeyboardInterrupt shutdown
    can leave background threads holding the stdin lock and produce fatal errors
    if Ctrl+C is pressed twice. os._exit(0) after logging avoids that.
    """

    def _handle_shutdown(signum, _frame) -> None:
        logger.info(
            "mcp_server_stopped",
            signal=signal.Signals(signum).name,
        )
        os._exit(0)

    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)


def main() -> None:
    """
    Boot logging, register MCP tools, and run the server until stopped.
    """

    setup_logging()
    args = parse_args()

    server = bootstrap_mcp_server()

    if args.transport in {"sse", "streamable-http"}:
        server.settings.host = args.host
        server.settings.port = args.port

    logger.info(
        "starting_mcp_server",
        name=server.name,
        transport=args.transport,
        host=args.host if args.transport != "stdio" else None,
        port=args.port if args.transport != "stdio" else None,
    )

    _register_shutdown_handlers()

    try:
        if args.transport in {"sse", "streamable-http"}:
            _run_http(server, args)
        else:
            server.run(transport=args.transport)
    except KeyboardInterrupt:
        logger.info("mcp_server_stopped", signal="KeyboardInterrupt")
        os._exit(0)


def _run_http(server, args) -> None:
    """
    Serve an HTTP transport behind the bearer-token auth middleware.

    HTTP_AUTH_MODE controls behaviour: "github" validates GitHub tokens,
    "static" accepts only MCP_STATIC_TOKENS, "off" disables auth (dev only).
    """

    import uvicorn

    from app.auth.middleware import BearerAuthMiddleware

    if settings.HTTP_AUTH_MODE == "off":
        logger.warning(
            "http_auth_disabled",
            hint="Set HTTP_AUTH_MODE=github (or static) before public deployment.",
        )

    app = (
        server.streamable_http_app()
        if args.transport == "streamable-http"
        else server.sse_app()
    )
    app.add_middleware(BearerAuthMiddleware)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_config=None,
    )


if __name__ == "__main__":
    main()
