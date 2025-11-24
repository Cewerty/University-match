"""
Database middleware.

Provides a per-update SQLAlchemy AsyncSession and injects it into the handler
context as "db_session". The session is created and closed automatically for
each incoming event.
"""

from collections.abc import AsyncGenerator
from typing import Any

from aiogram import BaseMiddleware
from sqlalchemy import Update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import get_session
from ..core.database import async_session_maker


class DatabaseMiddleware(BaseMiddleware):
    """Create and inject a database session for each request."""

    def __init__(self) -> None:
        """Инициализирует middleware с фабрикой сессий."""
        self.session_maker = async_session_maker

    async def __call__(
        self,
        handler: dict[str, Any],
        event: Update,
        data: Any,
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Open a DB session, inject it into data, and call the next handler.

        The session is exposed to downstream handlers via data["db_session"] and
        is closed automatically after the handler completes.

        Args:
            handler: The next handler in the middleware chain.
            event: The incoming update to process.
            data: A mutable context dictionary passed along the chain.

        Returns:
            AsyncGenerator[AsyncSession, None]: The result returned by the next handler.

        """
        async with get_session() as session:
            data["db_session"] = session
            return await handler(event, data)
