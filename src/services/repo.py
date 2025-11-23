from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core.models import Faculty, Group, Interest, User


async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int):
    result = await db.execute(
        select(User)
        .where(User.telegram_id == telegram_id)
        .options(selectinload(User.interests))  # 👈 Предварительная загрузка
    )
    return result.scalars().first()


async def get_faculty_by_id(db: AsyncSession, faculty_id: int):
    result = await db.execute(select(Faculty).where(Faculty.id == faculty_id))
    return result.scalars().first()


async def get_group_by_id(db: AsyncSession, group_id: int):
    result = await db.execute(select(Group).where(Group.id == group_id))
    return result.scalars().first()


async def get_all_faculties(db: AsyncSession):
    result = await db.execute(select(Faculty))
    return result.scalars().all()


async def get_groups_by_faculty(db: AsyncSession, faculty_id: int):
    result = await db.execute(select(Group).where(Group.faculty_id == faculty_id))
    return result.scalars().all()


async def get_all_interests(db: AsyncSession):
    result = await db.execute(select(Interest))
    return result.scalars().all()


async def create_user(
    db: AsyncSession,
    telegram_id: int,
    first_name: str,
    second_name: str,
    surname: str,
    faculty_id: int,
    group_id: int,
    interest_ids: list[int],
):
    existing_user_result = await db.execute(
        select(User)
        .where(User.telegram_id == telegram_id)
        .options(selectinload(User.interests))  # 👈 Предварительная загрузка
    )
    existing_user = existing_user_result.scalars().first()

    interests_result = await db.execute(select(Interest).where(Interest.id.in_(interest_ids)))
    interests = interests_result.scalars().all()

    if existing_user:
        # Обновляем существующего пользователя
        existing_user.first_name = first_name
        existing_user.second_name = second_name
        existing_user.surname = surname
        existing_user.faculty_id = faculty_id
        existing_user.group_id = group_id
        existing_user.interests = interests  # ✅ Теперь это сработает
        await db.commit()
        await db.refresh(existing_user)
        return existing_user

    # Создаем нового пользователя
    db_user = User(
        telegram_id=telegram_id,
        first_name=first_name,
        second_name=second_name,
        surname=surname,
        faculty_id=faculty_id,
        group_id=group_id,
        interests=interests,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user(db: AsyncSession, user: User, update_data: dict):
    for key, value in update_data.items():
        if key == "interest_ids":
            interests_result = await db.execute(select(Interest).where(Interest.id.in_(value)))
            interests = interests_result.scalars().all()
            user.interests = interests
        elif hasattr(user, key):
            setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user_by_telegram_id(db: AsyncSession, telegram_id: int):
    user_to_delete = await get_user_by_telegram_id(db, telegram_id)
    if user_to_delete:
        await db.delete(user_to_delete)
        await db.commit()
        return True
    return False
