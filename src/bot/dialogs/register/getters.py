"""
Getters module for the registration dialog.

Contains functions that retrieve data to display in the registration interface.
"""

from typing import Any

from aiogram_dialog import DialogManager, StartMode

from src.bot.states import MainMenuSM

from ....services.repo import (
    get_all_faculties,
    get_all_interests,
    get_groups_by_faculty,
    get_user_by_telegram_id,
)


async def get_faculties(**kwargs: dict[str, Any]) -> dict[str, Any]:
    """
    Fetch the list of faculties for UI display.

    Args:
        **kwargs: Additional parameters passed by aiogram_dialog.

    Returns:
        dict[str, Any]: A dictionary containing faculty data.

    """
    session = kwargs["db_session"]
    faculties = await get_all_faculties(session)
    return {"faculties": [(str(f.id), f.name) for f in faculties]}


async def get_faculty_groups(**kwargs: dict[str, Any]) -> dict[str : list[tuple[str, str]]]:
    """
    Fetch the list of groups for the selected faculty.

    Args:
        dialog_manager (DialogManager): Dialog manager instance.
        **kwargs: Additional parameters passed by aiogram_dialog.

    Returns:
        dict[str, Any]: A dictionary containing group data.

    """
    session = kwargs["db_session"]
    faculty_id = int(kwargs["faculty_id"])
    groups = await get_groups_by_faculty(session, faculty_id)
    return {"groups": [(str(f.id), f.name) for f in groups]}


async def get_interests(**kwargs: dict[str, Any]) -> dict[str : list[tuple[str]]]:
    """
    Fetch the list of interests for user selection.

    Args:
        **kwargs: Additional parameters passed by aiogram_dialog.

    Returns:
        dict[str, Any]: A dictionary containing interest data.

    """
    session = kwargs["db_session"]
    interets = await get_all_interests(session)
    return {"interets": [(str(f.id), f.name) for f in interets]}


async def on_register_dialog_start(start_data: Any, manager: DialogManager) -> None:
    """
    Obtain initial data for the registration dialog.

    Args:
        start_data (Any): Initial data passed by aiogram_dialog.
        manager (DialogManager): Dialog manager instance from aiogram_dialog.

    """
    manager.dialog_data["user_id"] = manager.event.from_user.id
    session = manager.middleware_data["db_session"]
    user = await get_user_by_telegram_id(session, manager.event.from_user.id)
    # TODO
    if user:
        await manager.done()
        await manager.start(MainMenuSM.main, mode=StartMode.RESET_STACK)
