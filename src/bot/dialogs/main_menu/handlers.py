"""
Callback handlers for main menu dialog interactions.

This module contains callback handlers for user interactions in the main menu,
including search functionality, match selection, and navigation.
"""

import operator
import time
from http import HTTPStatus
from typing import Any

import aiohttp
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from ....core import logger
from ....core.config import config
from ....core.models import User
from ....services.repo import get_faculty_by_id, get_group_by_id, get_user_by_id
from ...states import MainMenuSM


async def on_search_clicked(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    """
    Handle search button click and fetch user matches from API.

    Args:
        callback: The callback query from button click.
        button: The button widget that was clicked.
        manager: Dialog manager for controlling dialog flow.

    Raises:
        Exception: If connection to search server fails.

    """
    user_data = manager.dialog_data.get("data")
    user_id = user_data.id

    backend_url: str = config.BACKEND_URL.rstrip("/")

    logger.info(f"🌐 HTTP запрос к FastAPI для поиска пользователя {user_id}")
    logger.debug(f"🔗 URL запроса: http://{backend_url}/search/{user_id}")

    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        try:
            elapsed = time.time() - start_time
            async with session.get(f"http://{backend_url}/search/{user_id}") as resp:
                logger.info(f"⏱️ Ответ от FastAPI получен за {elapsed:.2f} секунд, статус: {resp.status}")
                if resp.status == HTTPStatus.GATEWAY_TIMEOUT:
                    error_text = await resp.text()
                    logger.error(f"🔍 Ошибка API поиска: {resp.status} - {error_text}")
                    await callback.message.answer("Система еще запускается, попробуй через минуту ⏳")
                    return

                if resp.status == HTTPStatus.NOT_FOUND:
                    error_text = await resp.text()
                    logger.error(f"🔍 Ошибка API поиска: {resp.status} - {error_text}")
                    await callback.message.answer(
                        "📊 Система еще обрабатывает ваши данные...\n\n"
                        "Пожалуйста, подождите 1-2 минуты и попробуйте снова. "
                        "Ваш профиль был успешно создан, но для поиска нужны дополнительные вычисления."
                    )
                    return

                if resp.status != HTTPStatus.OK:
                    error_text = await resp.text()
                    logger.error(f"🔍 Ошибка API поиска: {resp.status} - {error_text}")
                    await callback.message.answer(
                        "❌ Возникла временная ошибка при поиске.\n\n"
                        "Мы уже работаем над ее исправлением. Попробуйте снова через минуту."
                    )
                    return

                data = await resp.json()
                results = data.get("results", [])

                if not results:
                    await callback.message.answer(
                        "🔍 Поиск завершен, но пока нет подходящих совпадений.\n\n"
                        "Это может быть по нескольким причинам:\n"
                        "• Система еще обрабатывает ваши данные\n"
                        "• У вас уникальные интересы, и мы ищем подходящих людей\n"
                        "• В базе пока мало пользователей с похожими интересами\n\n"
                        "💡 Совет: обновите поиск через 1-2 минуты или добавьте больше интересов в профиль!"
                    )
                    return

                manager.dialog_data["user_matches"] = results
                await manager.switch_to(MainMenuSM.matches_select)

        except Exception:
            await callback.message.answer("Ошибка соединения с сервером поиска")


async def on_match_selected(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str) -> None:
    """
    Handle selection of a specific match from search results.

    Args:
        callback: The callback query from selection.
        widget: The widget that triggered the callback.
        manager: Dialog manager for controlling dialog flow.
        item_id: ID of the selected user match.

    """
    session = manager.middleware_data["db_session"]

    match_data: User = await get_user_by_id(session, item_id)

    manager.dialog_data["match_data"] = match_data
    manager.dialog_data["match_group"] = await get_group_by_id(session, match_data.group_id)
    manager.dialog_data["match_faculty"] = await get_faculty_by_id(session, match_data.faculty_id)
    manager.dialog_data["match_interests"] = list(map(operator.attrgetter("name"), match_data.interests))

    await manager.next()


async def send_profile(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    """
    Navigate to user profile view.

    Args:
        callback: The callback query from button click.
        button: The button widget that was clicked.
        manager: Dialog manager for controlling dialog flow.

    """
    await manager.switch_to(MainMenuSM.profile)


async def send_events(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    """
    Navigate to events view.

    Args:
        callback: The callback query from button click.
        button: The button widget that was clicked.
        manager: Dialog manager for controlling dialog flow.

    """
    await manager.switch_to(MainMenuSM.events)


async def back_to_menu(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    """
    Navigate back to main menu.

    Args:
        callback: The callback query from button click.
        button: The button widget that was clicked.
        manager: Dialog manager for controlling dialog flow.

    """
    await manager.switch_to(MainMenuSM.main)
