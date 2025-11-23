from typing import Any

from aiogram.types import CallbackQuery, Contact, KeyboardButton, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button

from ....services.repo import create_user
from ...states import MainMenuSM


async def on_second_name_received(message: Message, message_input: MessageInput, manager: DialogManager):
    manager.dialog_data["second_name"] = message.text
    await manager.next()


async def on_first_name_received(message: Message, message_input: MessageInput, manager: DialogManager):
    manager.dialog_data["first_name"] = message.text
    await manager.next()


async def on_surname_received(message: Message, message_input: MessageInput, manager: DialogManager):
    manager.dialog_data["surname"] = message.text
    await manager.next()


async def send_contact_request(callback: CallbackQuery, button: Button, manager: DialogManager):
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Share Contact", request_contact=True))
    await callback.message.answer(
        "Ваш контакт:", reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )


async def send_interest(callback: CallbackQuery, button: Button, manager: DialogManager):
    session = manager.middleware_data["db_session"]
    telegram_id = int(manager.dialog_data["user_id"])
    first_name = manager.dialog_data["first_name"]
    second_name = manager.dialog_data["second_name"]
    surname = manager.dialog_data["surname"]
    faculty_id = int(manager.dialog_data["faculty_id"])
    group_id = int(manager.dialog_data["group_id"])
    interest_ids = list(map(int, manager.dialog_data["interests"]))
    await create_user(session, telegram_id, first_name, second_name, surname, faculty_id, group_id, interest_ids)
    manager.middleware_data["user_id"] = manager.event.from_user.id
    await manager.done()
    await manager.start(MainMenuSM.main)


async def on_faculty_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    manager.middleware_data["faculty_id"] = item_id
    manager.dialog_data["faculty_id"] = item_id
    await manager.next()


async def on_group_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    manager.dialog_data["group_id"] = item_id
    await manager.next()


async def on_interest_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    list_of_interests = widget.get_checked()
    manager.dialog_data["interests"] = list_of_interests


async def on_other_messages(message: Message, message_input: MessageInput, manager: DialogManager):
    await message.answer("Please input correct value.")


async def on_contact_received(message: Message, message_input: MessageInput, manager: DialogManager):
    contact: Contact = message.contact
    manager.dialog_data["phone_number"] = contact.phone_number
    await manager.next()
