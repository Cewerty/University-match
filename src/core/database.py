"""
Database session factory and async context manager.

This module configures the SQLAlchemy AsyncEngine and session factory used by
the application. It exposes:
- engine: an AsyncEngine created from the configured DATABASE_URL.
- async_session: a sessionmaker that produces AsyncSession instances with
  expire_on_commit=False.

Use get_session() as an async context manager to obtain a per-operation
AsyncSession with automatic commit/rollback handling.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ..core.config import config


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""

    pass


engine = create_async_engine(config.DATABASE_URL)

async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an AsyncSession with automatic transaction management.

    The session is committed if the context exits successfully; on error, a
    rollback is issued and the original exception is re-raised. The session is
    always closed at the end of the context.

    Yields:
        AsyncSession: The active database session.

    Raises:
        Exception: Re-raised after issuing a rollback if an error occurs.

    Example:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))

    """
    session = async_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
