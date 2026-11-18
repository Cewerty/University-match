"""repo.create_user against an in-memory SQLite database."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import User
from src.services.repo import create_user, delete_user_by_telegram_id, get_user_by_id, get_user_by_telegram_id


def user_kwargs(catalog: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    interests = catalog["interests"]
    return {
        "telegram_id": 42,
        "first_name": "Иван",
        "second_name": "Петров",
        "surname": "Сергеевич",
        "phone_number": "+79000000000",
        "faculty_id": catalog["faculty"].id,
        "group_id": catalog["group"].id,
        "interest_ids": [interests["a"].id, interests["b"].id],
        **overrides,
    }


async def test_create_user_persists_user_with_interests(session: AsyncSession, catalog: dict[str, Any]) -> None:
    await create_user(session, **user_kwargs(catalog))

    user = await get_user_by_telegram_id(session, 42)
    assert user is not None
    assert (user.first_name, user.second_name) == ("Иван", "Петров")
    assert sorted(i.name for i in user.interests) == ["a", "b"]


async def test_create_user_updates_existing_user_instead_of_duplicating(
    session: AsyncSession, catalog: dict[str, Any]
) -> None:
    await create_user(session, **user_kwargs(catalog))
    await create_user(
        session,
        **user_kwargs(catalog, first_name="Пётр", interest_ids=[catalog["interests"]["c"].id]),
    )

    count = await session.scalar(select(func.count()).select_from(User))
    user = await get_user_by_telegram_id(session, 42)
    assert count == 1
    assert user is not None
    assert user.first_name == "Пётр"
    assert [i.name for i in user.interests] == ["c"]


async def test_lookups_return_none_for_unknown_user(session: AsyncSession) -> None:
    assert await get_user_by_telegram_id(session, 404) is None
    assert await get_user_by_id(session, 404) is None


async def test_delete_user_reports_whether_anything_was_deleted(session: AsyncSession, catalog: dict[str, Any]) -> None:
    await create_user(session, **user_kwargs(catalog))

    assert await delete_user_by_telegram_id(session, 42) is True
    assert await get_user_by_telegram_id(session, 42) is None
    assert await delete_user_by_telegram_id(session, 42) is False
