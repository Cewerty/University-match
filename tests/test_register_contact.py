"""Registration accepts only the sender's own contact, not a forwarded or hand-attached card."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.bot.dialogs.register.handlers import on_contact_received

SENDER_ID = 111


def make_update(contact_user_id: int | None, sender_id: int | None = SENDER_ID):
    contact = SimpleNamespace(phone_number="+79000000000", user_id=contact_user_id)
    from_user = SimpleNamespace(id=sender_id) if sender_id is not None else None
    message = SimpleNamespace(contact=contact, from_user=from_user, answer=AsyncMock())
    manager = SimpleNamespace(dialog_data={}, next=AsyncMock())
    return message, manager


async def test_own_contact_is_accepted() -> None:
    message, manager = make_update(contact_user_id=SENDER_ID)

    await on_contact_received(message, None, manager)

    assert manager.dialog_data["phone_number"] == "+79000000000"
    manager.next.assert_awaited_once()
    message.answer.assert_not_awaited()


@pytest.mark.parametrize("foreign_user_id", [222, None])
async def test_foreign_contact_is_rejected(foreign_user_id: int | None) -> None:
    """Another user's card, or a card of someone without a Telegram account (user_id is None)."""
    message, manager = make_update(contact_user_id=foreign_user_id)

    await on_contact_received(message, None, manager)

    assert "phone_number" not in manager.dialog_data
    manager.next.assert_not_awaited()
    message.answer.assert_awaited_once()


async def test_message_without_sender_is_rejected() -> None:
    message, manager = make_update(contact_user_id=SENDER_ID, sender_id=None)

    await on_contact_received(message, None, manager)

    assert "phone_number" not in manager.dialog_data
    manager.next.assert_not_awaited()
