"""
Seed the local development database with demo data.

This module initializes a synchronous SQLAlchemy engine derived from the project's
DATABASE_URL (converted from async to sync), and populates the database with:
- a predefined set of interests,
- faculties and groups,
- and 30 users with realistic Russian data using Faker (ru_RU).

If the database already contains 30 or more users, seeding is skipped.
"""

import random

from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import config
from src.core.models import Base, Faculty, Group, Interest, User

sync_db_url = config.DATABASE_URL.replace("+aiosqlite", "")

engine = create_engine(sync_db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

fake = Faker("ru_RU")

RUSSIAN_UPPERCASE_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"


def generate_unique_group_name(faculty: Faculty, existing_names: list[str]) -> str | None:
    """
    Generate a unique group name for a given faculty.

    Args:
        faculty (Faculty): The faculty object to generate a prefix from.
        existing_names (list[str]): A list of already existing group names.

    Returns:
        str | None: A unique group name, or None if max attempts exceeded.

    """
    faculty_prefix = faculty.name[:2].upper()
    max_attempts = 100

    for _ in range(max_attempts):
        random_letter = random.choice(RUSSIAN_UPPERCASE_ALPHABET)
        group_name = f"{faculty_prefix}-{random_letter}"

        if group_name not in existing_names:
            return group_name


def _seed_interests(db: Session) -> list[Interest]:
    """Seed interests into the database."""
    interest_names = [
        "Программирование",
        "Python",
        "Веб-дизайн",
        "Data Science",
        "Робототехника",
        "Геймдев",
        "Футбол",
        "Баскетбол",
        "Горные лыжи",
        "Тренажерный зал",
        "Йога",
        "Фотография",
        "Рисование",
        "Игра на гитаре",
        "Кулинария",
        "Настольные игры",
        "Аниме",
        "Научная фантастика",
        "Психология",
        "Путешествия по России",
        "Кино",
    ]
    existing_interests = {i.name for i in db.query(Interest).all()}
    new_interests = [Interest(name=n) for n in interest_names if n not in existing_interests]

    if new_interests:
        db.add_all(new_interests)
        db.commit()
        print(f"✅ Добавлено {len(new_interests)} новых интересов.")

    return db.query(Interest).all()


def _seed_faculties_and_groups(db: Session) -> list[Group]:
    """Seed faculties and groups into the database."""
    faculty_names = ["АВТФ", "ФЛА", "МТФ", "ФМА", "ФПМИ", "ФТФ", "ФБ❤️", "ФГО", "ИСТ", "РЭФ"]
    faculties: list[Faculty] = []

    if not db.query(Faculty).first():
        for name in faculty_names:
            faculty = Faculty(name=name)
            faculties.append(faculty)
            db.add(faculty)

        db.commit()

        all_groups = []
        existing_group_names = {g.name for g in db.query(Group).all()}
        for faculty in faculties:
            num_groups = random.randint(3, 5)

            for _ in range(num_groups):
                group_name = generate_unique_group_name(faculty, list(existing_group_names))
                if group_name:
                    existing_group_names.add(group_name)
                    group = Group(name=group_name, faculty_id=faculty.id)
                    all_groups.append(group)

        db.add_all(all_groups)
        db.commit()
        print(f"✅ Добавлено {len(all_groups)} групп для факультетов.")
        print("📋 Список созданных групп:")
        for group in all_groups:
            faculty = next(f for f in faculties if f.id == group.faculty_id)
            print(f"   • {group.name} ({faculty.name})")

    return db.query(Group).all()


def _seed_users(db: Session, amount: int, all_interests: list[Interest], all_groups: list[Group]) -> None:
    """Seed users with random attributes."""
    users_to_create = []

    print(f"🎲 Генерация {amount} пользователей...")

    for _ in range(amount):
        random_group = random.choice(all_groups)
        user_interests = random.sample(all_interests, k=random.randint(2, 5))

        user = User(
            telegram_id=random.randint(100000000, 999999999),
            first_name=fake.first_name(),
            second_name=fake.last_name(),
            surname=fake.middle_name(),
            phone_number=fake.phone_number(),
            faculty_id=random_group.faculty_id,
            group_id=random_group.id,
            interests=user_interests,
        )
        users_to_create.append(user)

    db.add_all(users_to_create)
    db.commit()

    print(f"🎉 Успешно добавлено {amount} пользователей с интересами!")


def seed_data() -> None:
    """
    Seed the database with demo data.

    Ensures tables are created, inserts interests if missing, creates faculties
    and groups if absent, and generates n-number users with random attributes and 2–5
    interests each. If there are already n-number or more users, the operation is
    skipped.

    Returns:
        None

    """
    print(f"🚀 Подключение к БД (Sync mode): {sync_db_url}")
    print("🚀 Начало наполнения базы данных...")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    user_generations_amount: int = config.SEED_GENERATION_AMOUNT

    try:
        if db.query(User).count() >= user_generations_amount:
            print("⚠️ База данных уже содержит достаточно пользователей. Пропускаем.")
            return

        def run_seeders(session: Session) -> None:
            """Apply composition to run operations."""
            all_interests_objs = _seed_interests(session)
            all_groups = _seed_faculties_and_groups(session)
            _seed_users(session, user_generations_amount, all_interests_objs, all_groups)

        run_seeders(db)

    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
