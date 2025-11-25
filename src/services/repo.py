"""
Data access (CRUD) module for User, Faculty, Group, and Interest entities.

Provides asynchronous functions to retrieve, create, update, and delete users,
as well as to fetch faculties, groups, and interests.
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..core import logger
from ..core.models import Faculty, Group, Interest, User


async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> User | None:
    """
    Get a user by telegram_id.

    Args:
        db (AsyncSession): SQLAlchemy async session.
        telegram_id (int): Telegram user identifier.

    Returns:
        User | None: User object with interests loaded, or None if not found.

    """
    try:
        logger.debug(f"🔍 Поиск пользователя по telegram_id: {telegram_id}")
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id).options(selectinload(User.interests))
        )
        user = result.scalars().first()
        if user:
            logger.info(f"✅ Найден пользователь ID={user.id}, telegram_id={telegram_id}")
            return user
        else:
            logger.warning(f"⚠️ Пользователь с telegram_id={telegram_id} не найден")
    except Exception as e:
        logger.error(f"❌ Ошибка при поиске пользователя по telegram_id={telegram_id}: {e!r}")
        raise


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """
    Get a user by database id.

    Args:
        db (AsyncSession): SQLAlchemy async session.
        user_id (int): User identifier in the database.

    Returns:
        User | None: User object with interests loaded, or None if not found.

    """
    try:
        logger.debug(f"🔍 Поиск пользователя по id: {user_id}")
        result = await db.execute(select(User).where(User.id == user_id).options(selectinload(User.interests)))
        user = result.scalars().first()
        if user:
            logger.info(f"✅ Найден пользователь ID={user.id}")
            return user
        else:
            logger.warning(f"⚠️ Пользователь с id={user_id} не найден")
    except Exception as e:
        logger.error(f"❌ Ошибка при поиске пользователя по id={user_id}: {e!r}")
        raise


async def get_faculty_by_id(db: AsyncSession, faculty_id: int) -> Faculty | None:
    """
    Get a faculty by id.

    Args:
        db (AsyncSession): SQLAlchemy async session.
        faculty_id (int): Faculty identifier.

    Returns:
        Faculty | None: Faculty object or None if not found.

    """
    result = await db.execute(select(Faculty).where(Faculty.id == faculty_id))
    return result.scalars().first()


async def get_group_by_id(db: AsyncSession, group_id: int) -> Group | None:
    """
    Get a group by id.

    Args:
        db (AsyncSession): SQLAlchemy async session.
        group_id (int): Group identifier.

    Returns:
        Group | None: Group object or None if not found.

    """
    result = await db.execute(select(Group).where(Group.id == group_id))
    return result.scalars().first()


async def get_all_faculties(db: AsyncSession) -> Sequence[Faculty]:
    """
    Get all faculties.

    Args:
        db (AsyncSession): SQLAlchemy async session.

    Returns:
        list[Faculty]: List of Faculty objects.

    """
    result = await db.execute(select(Faculty))
    return result.scalars().all()


async def get_groups_by_faculty(db: AsyncSession, faculty_id: int) -> Sequence[Group]:
    """
    Get all groups for a given faculty.

    Args:
        db (AsyncSession): SQLAlchemy async session.
        faculty_id (int): Faculty identifier.

    Returns:
        list[Group]: List of groups belonging to the faculty.

    """
    result = await db.execute(select(Group).where(Group.faculty_id == faculty_id))
    return result.scalars().all()


async def get_all_interests(db: AsyncSession) -> Sequence[Interest]:
    """
    Get all interests.

    Args:
        db (AsyncSession): SQLAlchemy async session.

    Returns:
        list[Interest]: List of Interest objects.

    """
    result = await db.execute(select(Interest))
    return result.scalars().all()


async def create_user(  # noqa: PLR0913, PLR0917
    db: AsyncSession,
    telegram_id: int,
    first_name: str,
    second_name: str,
    surname: str,
    phone_number: str,
    faculty_id: int,
    group_id: int,
    interest_ids: list[int],
) -> User:
    """
    Create a new user or update an existing one by telegram_id.

    If a user with the given telegram_id exists, their fields are updated with
    the provided values, including the list of interests. Otherwise, a new user
    is created.

    Args:
        db (AsyncSession): SQLAlchemy async session.
        telegram_id (int): Telegram ID of the user.
        first_name (str): First name.
        second_name (str): Last name (family name).
        surname (str): Patronymic/middle name.
        phone_number (str): Phone number.
        faculty_id (int): Faculty identifier.
        group_id (int): Group identifier.
        interest_ids (list[int]): List of interest identifiers.

    Returns:
        User: The created or updated User object.

    """
    existing_user_result = await db.execute(
        select(User).where(User.telegram_id == telegram_id).options(selectinload(User.interests))
    )
    existing_user = existing_user_result.scalars().first()

    interests_result = await db.execute(select(Interest).where(Interest.id.in_(interest_ids)))
    interests = interests_result.scalars().all()

    if existing_user:
        existing_user.first_name = first_name
        existing_user.second_name = second_name
        existing_user.surname = surname
        existing_user.phone_number = phone_number
        existing_user.faculty_id = faculty_id
        existing_user.group_id = group_id
        existing_user.interests = interests

        await db.commit()
        await db.refresh(existing_user)
        return existing_user

    # Create a new user
    db_user = User(
        telegram_id=telegram_id,
        first_name=first_name,
        second_name=second_name,
        surname=surname,
        phone_number=phone_number,
        faculty_id=faculty_id,
        group_id=group_id,
        interests=interests,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_user(db: AsyncSession, user: User, update_data: dict) -> User:
    """
    Update user fields.

    Supports updating simple fields and replacing the list of interests via the
    "interest_ids" key (list of interest identifiers).

    Args:
        db (AsyncSession): SQLAlchemy async session.
        user (User): Existing User object to update.
        update_data (dict): Dictionary of fields to update.

    Returns:
        User: The updated User object.

    """
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


async def delete_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> User | bool:
    """
    Delete a user by telegram_id.

    Args:
        db (AsyncSession): SQLAlchemy async session.
        telegram_id (int): Telegram ID of the user to delete.

    Returns:
        bool: True if the user was found and deleted, otherwise False.

    """
    user_to_delete = await get_user_by_telegram_id(db, telegram_id)
    if user_to_delete:
        await db.delete(user_to_delete)
        await db.commit()
        return True
    return False
