"""
Alembic environment script.

This module configures and runs database migrations in both offline and online
(asynchronous) modes. It integrates project settings and SQLAlchemy metadata
for autogeneration of migrations.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context
from src.core.config import config
from src.core.models import Base

# Alembic configuration object.
config_alembic = context.config

# Logger configuration.
if config_alembic.config_file_name is not None:
    fileConfig(config_alembic.config_file_name)

# Metadata for autogenerate.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in offline mode.

    In offline mode, migrations are emitted as SQL strings without opening a
    database connection. The database URL is taken from the project config.
    """
    url = config.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Help function to run migrations using a provided connection.

    Configures Alembic with the given synchronous connection and runs the
    migration scripts within a transaction.

    Args:
        connection (Connection): A synchronous SQLAlchemy connection.

    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in asynchronous mode.

    Creates an async engine from Alembic configuration, opens an async
    connection, and delegates migration execution to a synchronous context via
    connection.run_sync(do_run_migrations).
    """
    # Create the async engine.
    connectable = AsyncEngine(
        engine_from_config(
            config_alembic.get_section(config_alembic.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in online (asynchronous) mode.

    Wraps the asynchronous migration runner with asyncio.run().
    """
    import asyncio  # noqa: PLC0415

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
