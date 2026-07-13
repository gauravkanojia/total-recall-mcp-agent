"""
Utils for MCP Server containing various helper methods.
"""

from datetime import datetime
from zoneinfo import ZoneInfo


def get_timezone_info(time_zone="America/New_York"):
    """
    Get TimeZone Info literal for the timezone value provided
    """
    timezone_info = ZoneInfo(time_zone)

    return timezone_info


# Set your target timezone. In this case, EST/EDT
APP_TIMEZONE = ZoneInfo("America/New_York")


def get_timezone_stamper(logger, method_name, event_dict):
    """
    Get EST TimeZone Stamper in which the application is running.
    """

    # Generate the aware datetime and format it as ISO 8601
    event_dict["timestamp"] = datetime.now(APP_TIMEZONE).isoformat()
    return event_dict
