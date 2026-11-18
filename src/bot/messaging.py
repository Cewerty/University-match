"""
Helpers for replying to Telegram callbacks.

``CallbackQuery.message`` can be ``None`` or an ``InaccessibleMessage`` (the
original message is too old or was deleted), so calling ``.answer()`` on it
directly may fail. Handlers use ``answer_in_chat`` instead.
"""

from typing import Any

from aiogram.types import CallbackQuery, Message


async def answer_in_chat(callback: CallbackQuery, text: str, **kwargs: Any) -> None:
    """
    Send a message to the chat the callback came from.

    If the original message is no longer accessible, the text is shown as an
    alert to the user instead, so they still get a response. Extra keyword
    arguments (for example ``reply_markup``) are used only for the chat message.

    Args:
        callback: The callback query being handled.
        text: Text to send.
        **kwargs: Additional arguments for ``Message.answer``.

    """
    message = callback.message
    if isinstance(message, Message):
        await message.answer(text, **kwargs)
    else:
        await callback.answer(text, show_alert=True)
