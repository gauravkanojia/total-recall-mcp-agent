"""
Test Logging Configuration
"""

import structlog

from app.core.logging import setup_logging


def test_logging():
    """
    beta
    """
    # 1. Configure it first
    setup_logging()

    # 2. Get the bound logger instance
    logger = structlog.get_logger()

    # 3. Log your test message
    logger.info("mcp_logging_test", component="test", status="success")

    assert True
