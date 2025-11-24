"""
Callback handlers for main menu dialog interactions.

This module contains callback handlers for user interactions in the main menu,
including search functionality, match selection, and navigation.
"""

import operator
from http import HTTPStatus
from typing import Any

import aiohttp
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

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
    user_data: User = manager.dialog_data.get("data")
    user_id = user_data.id

    # Обращаемся к локальному API
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"http://localhost:8000/search/{user_id}") as resp:
                if resp.status == HTTPStatus.GATEWAY_TIMEOUT:
                    await callback.message.answer("Система еще запускается, попробуй через минуту ⏳")
                    return

                data = await resp.json()
                results = data.get("results", [])

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
