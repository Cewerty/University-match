import operator
from typing import Any

from aiogram_dialog import DialogManager, StartMode

from src.bot.states import MainMenuSM

from ....services.repo import (
    get_all_faculties,
    get_all_interests,
    get_faculty_by_id,
    get_group_by_id,
    get_groups_by_faculty,
    get_user_by_telegram_id,
)


async def get_faculties(**kwargs):
    session = kwargs["db_session"]
    faculties = await get_all_faculties(session)
    return {"faculties": [(str(f.id), f.name) for f in faculties]}


async def get_faculty_groups(**kwargs):
    session = kwargs["db_session"]
    faculty_id = int(kwargs["faculty_id"])
    groups = await get_groups_by_faculty(session, faculty_id)
    return {"groups": [(str(f.id), f.name) for f in groups]}


async def get_interests(**kwargs):
    session = kwargs["db_session"]
    interets = await get_all_interests(session)
    return {"interets": [(str(f.id), f.name) for f in interets]}


async def get_user_data(**kwargs):
    session = kwargs["db_session"]
    user_id = kwargs["user_id"]
    data = await get_user_by_telegram_id(session, user_id)
    group = await get_group_by_id(session, data.group_id)
    faculty = await get_faculty_by_id(session, data.faculty_id)
    interests = list(map(operator.attrgetter("name"), data.interests))
    return {"user_data": data, "group_name": group.name, "faculty_name": faculty.name, "interests_names": interests}


async def on_register_dialog_start(start_data: Any, manager: DialogManager):
    manager.dialog_data["user_id"] = manager.event.from_user.id
    session = manager.middleware_data["db_session"]
    user = await get_user_by_telegram_id(session, manager.event.from_user.id)
    # TODO
    if user:
        await manager.done()
        await manager.start(MainMenuSM.main, mode=StartMode.RESET_STACK)
