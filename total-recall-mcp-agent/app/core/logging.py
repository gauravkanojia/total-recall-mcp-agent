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
    """

    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(message)s",
        stream=sys.stdout,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            # structlog.processors.TimeStamper(fmt="iso"),
            get_timezone_stamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(pad_event_to=0),
            # structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(settings.LOG_LEVEL),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger()
