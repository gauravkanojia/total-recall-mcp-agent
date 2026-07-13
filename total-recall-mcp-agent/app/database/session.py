"""
Database Session Manager for the MCP Server's Cockroach DB
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.database.database import get_engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Return a session factory bound to the current engine.
    """
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session
