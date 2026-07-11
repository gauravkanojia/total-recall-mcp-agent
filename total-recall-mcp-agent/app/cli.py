from app.core.logging import setup_logging, logger
from app.mcp.server import create_mcp_server


def main():

    setup_logging()
    logger.info("starting_mcp_server")
    server = create_mcp_server()
    server.run()


if __name__ == "__main__":
    main()
