import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
import structlog

from app.core.config import settings


def timezone_stamper(logger, log_method, event_dict):
    # Set your target timezone
    tz = ZoneInfo("America/New_York")

    # Generate the aware datetime and format it as ISO 8601
    event_dict["timestamp"] = datetime.now(tz).isoformat()
    return event_dict


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
            structlog.processors.TimeStamper(fmt="iso"),
            timezone_stamper,
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
