from typing import Any

from aiogram import BaseMiddleware
from sqlalchemy import Update

from ..core import get_session


class DatabaseMiddleware(BaseMiddleware):
    """Middleware для автоматического создания сессии на каждый запрос."""

    async def __call__(self, handler: dict[str, Any], event: Update, data: Any):
        async with get_session() as session:
            data["db_session"] = session
            return await handler(event, data)
