"""
Data getters for main menu dialog.

This module provides data retrieval functions for the main menu dialog,
handling user profile data, match results, and match profile information.
Dialog data holds only JSON-serializable dicts; getters turn them back into
value objects for rendering.
"""

from typing import Any

from aiogram_dialog import DialogManager, StartMode
from sqlalchemy.ext.asyncio import AsyncSession

from ....core import logger
from ....core.config import config
from ....core.models import User
from ....core.value_objects import MatchCandidate, UserProfile
from ....services import get_faculty_by_id, get_group_by_id, get_user_by_telegram_id
from ...states import RegisterSM
from .keys import MATCH_PROFILE, MATCHES, PROFILE


async def load_profile(session: AsyncSession, user: User) -> UserProfile:
    """
    Load the user's faculty and group and build a profile value object.

    Args:
        session: Database session.
        user: User with interests loaded.

    Returns:
        UserProfile: Serializable snapshot of the user's profile.

    """
    faculty = await get_faculty_by_id(session, user.faculty_id)
    group = await get_group_by_id(session, user.group_id)
    return UserProfile.from_user(user, faculty, group)


async def on_main_menu_dialog_start(start_data: Any, manager: DialogManager) -> None:
    """
    Initialize main menu dialog with the current user's profile.

    If the user is not registered, the registration dialog is started instead.

    Args:
        start_data: Data passed when starting the dialog.
        manager: Dialog manager for accessing dialog data and middleware.

    """
    session: AsyncSession = manager.middleware_data["db_session"]
    telegram_id = manager.event.from_user.id  # type: ignore[union-attr]
    user = await get_user_by_telegram_id(session, telegram_id)
    if user is None:
        logger.warning(f"⚠️ Пользователь {telegram_id} открыл меню без регистрации")
        await manager.start(RegisterSM.GET_CONTACT, mode=StartMode.RESET_STACK)
        return

    manager.dialog_data[PROFILE] = (await load_profile(session, user)).to_dict()


async def get_main_menu_data(dialog_manager: DialogManager, **_: Any) -> dict[str, Any]:
    """Provide the current user's profile for the main menu greeting."""
    return {"profile": UserProfile.from_dict(dialog_manager.dialog_data[PROFILE])}


async def get_profile_data(dialog_manager: DialogManager, **_: Any) -> dict[str, Any]:
    """Provide the current user's profile for the profile window."""
    return {"profile": UserProfile.from_dict(dialog_manager.dialog_data[PROFILE])}


async def get_user_match(dialog_manager: DialogManager, **_: Any) -> dict[str, Any]:
    """
    Provide search results above the configured similarity threshold.

    Returns:
        Dictionary with a "matches" list of MatchCandidate objects.

    """
    candidates = (MatchCandidate.from_api(raw) for raw in dialog_manager.dialog_data.get(MATCHES, []))
    return {"matches": [c for c in candidates if c.is_relevant(config.MINIMAL_MATCH_VALUE)]}


async def get_match_profile_data(dialog_manager: DialogManager, **_: Any) -> dict[str, Any]:
    """Provide the selected match's profile, including contact information."""
    return {"profile": UserProfile.from_dict(dialog_manager.dialog_data[MATCH_PROFILE])}
