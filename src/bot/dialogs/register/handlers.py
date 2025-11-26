"""
Module of handlers for the registration dialog.

Contains functions that handle user actions during the registration process.
"""

from typing import Any

from aiogram.types import CallbackQuery, Contact, KeyboardButton, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button

from ....core.database import get_session

from ....core import logger
from ....services.repo import create_user
from ...states import MainMenuSM
from ....services.matcher import matcher_service

async def on_second_name_received(message: Message, message_input: MessageInput, manager: DialogManager) -> None:
    """
    Handle input of the second name (family name).

    Args:
        message (Message): The incoming message from the user.
        message_input (MessageInput): The message input widget instance.
        manager (DialogManager): The dialog manager.

    """
    manager.dialog_data["second_name"] = message.text
    await manager.next()


async def on_first_name_received(message: Message, message_input: MessageInput, manager: DialogManager) -> None:
    """
    Handle input of the first name.

    Args:
        message (Message): The incoming message from the user.
        message_input (MessageInput): The message input widget instance.
        manager (DialogManager): The dialog manager.

    """
    manager.dialog_data["first_name"] = message.text
    await manager.next()


async def on_surname_received(message: Message, message_input: MessageInput, manager: DialogManager) -> None:
    """
    Handle input of the patronymic (middle name).

    Args:
        message (Message): The incoming message from the user.
        message_input (MessageInput): The message input widget instance.
        manager (DialogManager): The dialog manager.

    """
    manager.dialog_data["surname"] = message.text
    await manager.next()


async def send_contact_request(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    """
    Send a keyboard requesting the user's contact.

    This sends a single-use reply keyboard with a "Share Contact" button
    that requests the user's contact information.

    Args:
        callback (CallbackQuery): The callback query that triggered this handler.
        button (Button): The widget button instance.
        manager (DialogManager): The dialog manager.

    """
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Share Contact", request_contact=True))
    await callback.message.answer(
        "Ваш контакт:", reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )


async def send_interest(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    """
    Registration handler.

    It is assumed that the phone number was saved in dialog_data in previous steps.

    Args:
        callback (CallbackQuery): The callback query that triggered this handler.
        button (Button): The widget button instance.
        manager (DialogManager): The dialog manager.

    """
    try:
        session = manager.middleware_data["db_session"]

        telegram_id = int(manager.dialog_data.get("user_id", callback.from_user.id))
        first_name = manager.dialog_data["first_name"]
        second_name = manager.dialog_data["second_name"]
        surname = manager.dialog_data.get("surname")

        phone_number = manager.dialog_data["phone_number"]

        faculty_id = int(manager.dialog_data["faculty_id"])
        group_id = int(manager.dialog_data["group_id"])
        interest_ids = list(map(int, manager.dialog_data["interests"]))

        user = await create_user(
            db=session,
            telegram_id=telegram_id,
            first_name=first_name,
            second_name=second_name,
            surname=surname,
            phone_number=phone_number,
            faculty_id=faculty_id,
            group_id=group_id,
            interest_ids=interest_ids,
        )

        logger.info(f"✅ Пользователь {user.id} успешно зарегистрирован")
        logger.info(f"🔍 Запуск обновления индекса для нового пользователя {user.id}")
        
        try:
            async with get_session() as session:
                if await matcher_service.add_user_to_index(session, user.id):
                    logger.info(f"Index для пользователя {user.id} успешно создан")
                else:
                    logger.error("Matcher не смог создать индекс")
        except Exception as e: 
            logger.error(f"❌ Ошибка при добавлении пользователя {user.id} в индекс: {e!r}")
        
        manager.middleware_data["user_id"] = telegram_id

        await manager.done()
        await manager.start(MainMenuSM.main)

    except Exception as e:
        logger.error(f"❌ Ошибка при регистрации пользователя {callback.from_user.id}: {e!r}")
        logger.exception("📋 Трейс ошибки регистрации")
        raise


async def on_faculty_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    """
    Handle faculty selection from the list.

    Stores the selected faculty id in both middleware_data and dialog_data,
    then advances the dialog to the next step.

    Args:
        callback (CallbackQuery): The callback query that triggered this handler.
        widget (Any): The widget instance that provided the selection.
        manager (DialogManager): The dialog manager.
        item_id (str): The id of the selected faculty item.

    """
    manager.middleware_data["faculty_id"] = item_id
    manager.dialog_data["faculty_id"] = item_id
    await manager.next()


async def on_group_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    """
    Handle group selection for the chosen faculty.

    Stores the selected group id in dialog_data and advances the dialog.

    Args:
        callback (CallbackQuery): The callback query that triggered this handler.
        widget (Any): The widget instance that provided the selection.
        manager (DialogManager): The dialog manager.
        item_id (str): The id of the selected group item.

    """
    manager.dialog_data["group_id"] = item_id
    await manager.next()


async def on_interest_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    """
    Handle interest (checkbox) selection changes.

    Retrieves the list of checked interests from the widget and stores it in dialog_data.

    Args:
        callback (CallbackQuery): The callback query that triggered this handler.
        widget (Any): The widget instance (should support get_checked()).
        manager (DialogManager): The dialog manager.
        item_id (str): The id of the toggled interest item.

    """
    list_of_interests = widget.get_checked()
    manager.dialog_data["interests"] = list_of_interests


async def on_other_messages(message: Message, message_input: MessageInput, manager: DialogManager) -> None:
    """
    Fallback handler for unexpected messages.

    Prompts the user to provide a correct value.

    Args:
        message (Message): The incoming message from the user.
        message_input (MessageInput): The message input widget instance.
        manager (DialogManager): The dialog manager.

    """
    await message.answer("Please input correct value.")


async def on_contact_received(message: Message, message_input: MessageInput, manager: DialogManager) -> None:
    """
    Handle a received contact message.

    Extracts the phone number from the Contact payload, stores it in dialog_data,
    and advances the dialog to the next step.

    Args:
        message (Message): The incoming message containing Contact.
        message_input (MessageInput): The message input widget instance.
        manager (DialogManager): The dialog manager.

    """
    contact: Contact = message.contact
    manager.dialog_data["phone_number"] = contact.phone_number
    await manager.next()
