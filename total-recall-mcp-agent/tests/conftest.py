import os

# Tests run each case in its own event loop; pooled connections cached across
# loops break asyncpg, so force NullPool before any app module loads settings.
os.environ.setdefault("DATABASE_USE_NULLPOOL", "true")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from db_probe import database_is_reachable  # noqa: E402
from fakes import (  # noqa: E402
    FakeMemoryRepository,
    FakeUserRepository,
    apply_mcp_executor_no_db_patches,
    make_test_user,
)

from app.database.database import dispose_engine  # noqa: E402
from app.mcp.executor import executor  # noqa: E402
from app.services.memory_service import MemoryService  # noqa: E402
from app.services.user_service import UserService  # noqa: E402


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: tests that require a reachable DATABASE_URL",
    )


def pytest_collection_modifyitems(config, items):
    if database_is_reachable():
        return

    reason = "DATABASE_URL is not reachable"
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)


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


@pytest.fixture
def fake_memory_repository():
    return FakeMemoryRepository()


@pytest.fixture
def patch_memory_service_repository(monkeypatch, fake_memory_repository):
    original_init = MemoryService.__init__

    def _init(self, session, embedding_provider):
        original_init(self, session, embedding_provider)
        self.repository = fake_memory_repository

    monkeypatch.setattr(MemoryService, "__init__", _init)
    return fake_memory_repository


@pytest.fixture
def patch_user_service_repository(monkeypatch):
    user = make_test_user()
    fake_repo = FakeUserRepository({user.principal_id: user})
    original_init = UserService.__init__

    def _init(self, session):
        original_init(self, session)
        self.repository = fake_repo

    monkeypatch.setattr(UserService, "__init__", _init)
    return fake_repo


@pytest.fixture
def patch_mcp_executor_no_db(monkeypatch):
    apply_mcp_executor_no_db_patches(monkeypatch)
