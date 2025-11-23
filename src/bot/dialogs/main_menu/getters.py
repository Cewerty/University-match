import operator
from typing import Any

from aiogram_dialog import DialogManager

from ....core import Faculty, Group, User
from ....services import get_faculty_by_id, get_group_by_id, get_user_by_telegram_id


async def on_main_menu_dialog_start(start_data: Any, manager: DialogManager):  # noqa: ANN401
    session = manager.middleware_data["db_session"]
    manager.dialog_data["user_id"] = manager.event.from_user.id
    user_id = manager.event.from_user.id
    manager.dialog_data["data"] = await get_user_by_telegram_id(session, user_id)
    data = manager.dialog_data["data"]
    manager.dialog_data["group"] = await get_group_by_id(session, data.group_id)
    manager.dialog_data["faculty"] = await get_faculty_by_id(session, data.faculty_id)
    manager.dialog_data["interests_names"] = list(map(operator.attrgetter("name"), data.interests))


async def get_profile_data(**kwargs):
    manager: DialogManager = kwargs["dialog_manager"]
    user_data: User = manager.dialog_data.get("data")

    first_name: str = user_data.first_name
    second_name: str = user_data.second_name
    surname: str = user_data.surname

    faculty_data: Faculty = manager.dialog_data.get("faculty")
    faculty_name: str = faculty_data.name

    group_data: Group = manager.dialog_data.get("group")
    group_name: str = group_data.name

    interests_names: list[str] = manager.dialog_data.get("interests_names")

    return {
        "first_name": first_name,
        "second_name": second_name,
        "surname": surname,
        "faculty": faculty_name,
        "group": group_name,
        "interests": interests_names,
    }


async def get_user_match(**kwargs: dict[str, Any]):
    manager: DialogManager = kwargs["dialog_manager"]
    user_matches_data: list[dict[str, Any]] = manager.dialog_data.get("user_matches")
    filtered_result = [(item["id"], item["name"]) for item in user_matches_data if item["score"] > 0.2]

    return {
        "matches": filtered_result,
    }


async def get_match_profile_data(**kwargs):
    manager: DialogManager = kwargs["dialog_manager"]
    user_data: User = manager.dialog_data.get("match_data")

    first_name: str = user_data.first_name
    second_name: str = user_data.second_name
    surname: str = user_data.surname
    phone_number: str = user_data.phone_number

    faculty_data: Faculty = manager.dialog_data.get("match_faculty")
    faculty_name: str = faculty_data.name

    group_data: Group = manager.dialog_data.get("match_group")
    group_name: str = group_data.name

    interests_names: list[str] = manager.dialog_data.get("match_interests")

    return {
        "first_name": first_name,
        "second_name": second_name,
        "surname": surname,
        "faculty": faculty_name,
        "group": group_name,
        "interests": interests_names,
        "phone_number": phone_number,
    }
