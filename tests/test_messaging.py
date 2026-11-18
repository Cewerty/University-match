"""answer_in_chat must not crash when the callback's original message is gone."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.types import Chat, InaccessibleMessage, Message

from src.bot.messaging import answer_in_chat


def make_callback(message: object) -> SimpleNamespace:
    return SimpleNamespace(message=message, answer=AsyncMock())


async def test_sends_to_chat_when_message_is_accessible(monkeypatch: pytest.MonkeyPatch) -> None:
    send = AsyncMock()
    monkeypatch.setattr(Message, "answer", send)
    message = Message(message_id=1, date=datetime.now(UTC), chat=Chat(id=1, type="private"))
    callback = make_callback(message)

    await answer_in_chat(callback, "hello", reply_markup="markup")  # type: ignore[arg-type]

    send.assert_awaited_once_with("hello", reply_markup="markup")
    callback.answer.assert_not_awaited()


@pytest.mark.parametrize(
    "message",
    [None, InaccessibleMessage(chat=Chat(id=1, type="private"), message_id=1)],
    ids=["no message", "inaccessible message"],
)
async def test_falls_back_to_alert_when_message_is_not_accessible(message: object) -> None:
    callback = make_callback(message)

    await answer_in_chat(callback, "hello")  # type: ignore[arg-type]

    callback.answer.assert_awaited_once_with("hello", show_alert=True)
