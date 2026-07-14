"""
Alembic migration environment configuration.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

# Import models so SQLAlchemy metadata is populated
from app.database.models import (
    Base,
    Memory,  # noqa: F401
    User,  # noqa: F401
)

# from app.database.models import Audit  # noqa: F401

config = context.config


# Use application settings instead of alembic.ini
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL,
)


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations without a database connection.
    """

    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """
    Run migrations using an active connection.
    """

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations using async database connection.
    """

    connectable = create_async_engine(
        settings.DATABASE_URL,
        connect_args={
            "ssl": False,
        },
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
