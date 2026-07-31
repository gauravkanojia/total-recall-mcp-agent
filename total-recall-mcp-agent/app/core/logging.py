"""
Setup Logger functionality for the MCP Server
"""

import logging
import sys

import structlog

from app.core.config import settings
from app.tools.utils import get_timezone_stamper


def setup_logging() -> None:
    """
    Configure structured application logging.

    Logs must go to stderr, not stdout. MCP stdio transport uses stdout
    exclusively for JSON-RPC messages; any log line on stdout breaks clients
    like Cursor.
    """

    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(message)s",
        stream=sys.stderr,
    )

    # Production: JSON lines with UTC timestamps — queryable in CloudWatch
    # Logs Insights. Development: human-readable console output in app TZ.
    if settings.ENVIRONMENT == "production":
        timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
        renderer = structlog.processors.JSONRenderer()
    else:
        timestamper = get_timezone_stamper
        renderer = structlog.dev.ConsoleRenderer(pad_event_to=0)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(settings.LOG_LEVEL),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger()
