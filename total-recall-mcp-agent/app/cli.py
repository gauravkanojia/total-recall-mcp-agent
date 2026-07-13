"""
Standalone entry point for the Total Recall MCP server.

This is what MCP clients (Cursor, Claude Desktop, etc.) launch directly,
typically over stdio:

    uv run total-recall-mcp
    uv run python -m app.cli
    uv run python -m app.cli --transport streamable-http --port 4646
"""

import argparse

from app.bootstrap import bootstrap_mcp_server
from app.core.config import settings
from app.core.logging import logger, setup_logging


def parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments, falling back to application settings.
    """

    parser = argparse.ArgumentParser(
        prog="total-recall-mcp",
        description="Run the Total Recall MCP agent server.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=settings.MCP_TRANSPORT,
        help="MCP transport to serve (default: %(default)s).",
    )

    return parser.parse_args()


def main() -> None:
    """
    Boot logging, register MCP tools, and run the server until stopped.
    """

    setup_logging()
    args = parse_args()

    server = bootstrap_mcp_server()

    logger.info(
        "starting_mcp_server",
        name=server.name,
        transport=args.transport,
    )

    try:
        server.run(transport=args.transport)
    except KeyboardInterrupt:
        logger.info("mcp_server_stopped")


if __name__ == "__main__":
    main()
