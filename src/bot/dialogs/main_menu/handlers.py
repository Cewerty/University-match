"""
Callback handlers for main menu dialog interactions.

This module contains callback handlers for user interactions in the main menu,
including search functionality, match selection, and navigation.
"""

import time
from http import HTTPStatus
from typing import Any

import aiohttp
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from ....core import logger
from ....core.config import config
from ....core.value_objects import MatchCandidate, UserProfile
from ....services.repo import get_user_by_id
from ...messaging import answer_in_chat
from ...states import MainMenuSM
from .getters import load_profile
from .keys import MATCH_PROFILE, MATCHES, PROFILE


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
    user_id = UserProfile.from_dict(manager.dialog_data[PROFILE]).id
    search_url = f"{config.BACKEND_URL}/search/{user_id}"

    logger.info(f"🌐 HTTP запрос к FastAPI для поиска пользователя {user_id}")
    logger.debug(f"🔗 URL запроса: {search_url}")

    start_time = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(search_url) as resp:
                elapsed = time.perf_counter() - start_time
                logger.info(f"⏱️ Ответ от FastAPI получен за {elapsed:.2f} секунд, статус: {resp.status}")
                if resp.status == HTTPStatus.SERVICE_UNAVAILABLE:
                    error_text = await resp.text()
                    logger.error(f"🔍 Ошибка API поиска: {resp.status} - {error_text}")
                    await answer_in_chat(callback, "Система еще запускается, попробуй через минуту ⏳")
                    return

                if resp.status == HTTPStatus.NOT_FOUND:
                    error_text = await resp.text()
                    logger.error(f"🔍 Ошибка API поиска: {resp.status} - {error_text}")
                    await answer_in_chat(
                        callback,
                        "📊 Система еще обрабатывает ваши данные...\n\n"
                        "Пожалуйста, подождите 1-2 минуты и попробуйте снова. "
                        "Ваш профиль был успешно создан, но для поиска нужны дополнительные вычисления.",
                    )
                    return

                if resp.status != HTTPStatus.OK:
                    error_text = await resp.text()
                    logger.error(f"🔍 Ошибка API поиска: {resp.status} - {error_text}")
                    await answer_in_chat(
                        callback,
                        "❌ Возникла временная ошибка при поиске.\n\n"
                        "Мы уже работаем над ее исправлением. Попробуйте снова через минуту.",
                    )
                    return

                data = await resp.json()
                results = data.get("results", [])

                if not results:
                    await answer_in_chat(
                        callback,
                        "🔍 Поиск завершен, но пока нет подходящих совпадений.\n\n"
                        "Это может быть по нескольким причинам:\n"
                        "• Система еще обрабатывает ваши данные\n"
                        "• У вас уникальные интересы, и мы ищем подходящих людей\n"
                        "• В базе пока мало пользователей с похожими интересами\n\n"
                        "💡 Совет: обновите поиск через 1-2 минуты или добавьте больше интересов в профиль!",
                    )
                    return

                manager.dialog_data[MATCHES] = [MatchCandidate.from_api(item).to_dict() for item in results]
                await manager.switch_to(MainMenuSM.matches_select)

        except Exception:
            await answer_in_chat(callback, "Ошибка соединения с сервером поиска")


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

    match_user = await get_user_by_id(session, int(item_id))
    if match_user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    profile = await load_profile(session, match_user)
    manager.dialog_data[MATCH_PROFILE] = profile.to_dict()

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
