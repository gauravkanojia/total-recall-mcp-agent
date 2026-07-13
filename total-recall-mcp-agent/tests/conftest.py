import pytest_asyncio

from app.database.database import dispose_engine
from app.mcp.executor import executor


@pytest_asyncio.fixture(
    scope="session",
    autouse=True,
)
async def cleanup_database_engine():
    """
    Cleanup DB Engine
    """

    executor.clear()
    yield
    await dispose_engine()
    executor.clear()


@pytest_asyncio.fixture(autouse=True)
def reset_mcp_tools():

    executor.clear()

    yield

    executor.clear()
