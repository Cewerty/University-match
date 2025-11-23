import random

from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import config
from src.core.models import Base, Faculty, Group, Interest, User

sync_db_url = config.DATABASE_URL.replace("+aiosqlite", "")

engine = create_engine(sync_db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

fake = Faker("ru_RU")


def seed_data():
    print(f"🚀 Подключение к БД (Sync mode): {sync_db_url}")
    print("🚀 Начало наполнения базы данных...")

    # Создаем таблицы
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Проверка на наличие данных
        if db.query(User).count() >= 30:
            print("⚠️ База данных уже содержит достаточно пользователей. Пропускаем.")
            return

        # --- 1. Создаем интересы ---
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

        all_interests_objs = db.query(Interest).all()

        # --- 2. Создаем факультеты и группы ---
        if not db.query(Faculty).first():
            f_it = Faculty(name="ФИИТ")
            f_hum = Faculty(name="ГумФак")
            f_eco = Faculty(name="Эконом")

            db.add(f_it)
            db.add(f_hum)
            db.add(f_eco)
            db.commit()

            groups = [
                Group(name="ИТ-21", faculty_id=f_it.id),
                Group(name="ИТ-22", faculty_id=f_it.id),
                Group(name="ГН-11", faculty_id=f_hum.id),
                Group(name="ЭК-31", faculty_id=f_eco.id),
            ]
            db.add_all(groups)
            db.commit()
            print("✅ Факультеты и группы созданы.")

        all_groups = db.query(Group).all()

        # --- 3. Генерация пользователей ---
        users_to_create = []

        print("🎲 Генерация 30 пользователей...")

        for _ in range(30):
            random_group = random.choice(all_groups)

            # Выбираем от 2 до 5 интересов
            user_interests = random.sample(all_interests_objs, k=random.randint(2, 5))

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

        print("🎉 Успешно добавлено 30 пользователей с интересами!")

    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
