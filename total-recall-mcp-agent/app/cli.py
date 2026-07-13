"""
MCP CLI init
"""

from app.core.logging import setup_logging, logger
from app.mcp.server import get_mcp_server


def main():
    """
    Main function to invoke CLI for MCP Server
    """
    setup_logging()
    logger.info("starting_mcp_server")
    server = get_mcp_server()
    server.run()


if __name__ == "__main__":
    main()
