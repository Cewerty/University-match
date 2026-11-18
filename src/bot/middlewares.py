"""
Database middleware.

Provides a per-update SQLAlchemy AsyncSession and injects it into the handler
context as "db_session". The session is created and closed automatically for
each incoming event.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from ..core import get_session


class DatabaseMiddleware(BaseMiddleware):
    """Create and inject a database session for each update."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Open a DB session, inject it into data, and call the next handler.

        The session is exposed to downstream handlers via data["db_session"] and
        is committed and closed automatically after the handler completes.

        Args:
            handler: The next handler in the middleware chain.
            event: The incoming Telegram event.
            data: A mutable context dictionary passed along the chain.

        Returns:
            Any: The result returned by the next handler.

        """
        async with get_session() as session:
            data["db_session"] = session
            return await handler(event, data)
