"""DatabaseMiddleware gives every update its own session and passes the handler's result through."""

from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.middlewares import DatabaseMiddleware


async def test_injects_a_session_and_returns_the_handler_result() -> None:
    seen: dict[str, Any] = {}

    async def handler(event: Any, data: dict[str, Any]) -> str:
        seen["session"] = data["db_session"]
        return "handled"

    result = await DatabaseMiddleware()(handler, SimpleNamespace(), {})  # type: ignore[arg-type]

    assert result == "handled"
    assert isinstance(seen["session"], AsyncSession)


async def test_each_update_gets_its_own_session() -> None:
    sessions: list[AsyncSession] = []

    async def handler(event: Any, data: dict[str, Any]) -> None:
        sessions.append(data["db_session"])

    middleware = DatabaseMiddleware()
    await middleware(handler, SimpleNamespace(), {})  # type: ignore[arg-type]
    await middleware(handler, SimpleNamespace(), {})  # type: ignore[arg-type]

    assert sessions[0] is not sessions[1]


async def test_handler_errors_propagate() -> None:
    async def handler(event: Any, data: dict[str, Any]) -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await DatabaseMiddleware()(handler, SimpleNamespace(), {})  # type: ignore[arg-type]
