from app.core.logging import logger, setup_logging

"""
Test Logging Configuration
"""


def test_logging():

    setup_logging()
    logger.info("mcp_logging_test", component="test", status="success")
    assert True
