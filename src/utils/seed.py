from models import Base, Faculty, Group, Interest, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.config import config

engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_data():
    # Создаем таблицы
    print("Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы.")

    db = SessionLocal()

    try:
        # Проверяем, есть ли уже данные
        if db.query(Faculty).first():
            print("База данных уже заполнена. Пропускаем.")
            return

        print("Наполнение базы данных тестовыми данными...")

        # 1. Создаем интересы
        interests = [Interest(name=n) for n in ["Программирование", "Дизайн", "Музыка", "Спорт", "Кино", "Путешествия"]]
        db.add_all(interests)
        db.commit()

        # 2. Создаем факультеты и группы
        f1 = Faculty(name="Факультет информационных технологий")
        f2 = Faculty(name="Факультет гуманитарных наук")

        g1_1 = Group(name="ИТ-21", faculty=f1)
        g1_2 = Group(name="ИТ-22", faculty=f1)
        g2_1 = Group(name="ГН-11", faculty=f2)

        db.add_all([f1, f2, g1_1, g1_2, g2_1])
        db.commit()

        prog_interest = db.query(Interest).filter_by(name="Программирование").one()
        music_interest = db.query(Interest).filter_by(name="Музыка").one()
        travel_interest = db.query(Interest).filter_by(name="Путешествия").one()

        user1 = User(
            telegram_id=12345,
            first_name="Иван",
            second_name="Иванов",
            faculty_id=f1.id,
            group_id=g1_1.id,
            interests=[prog_interest, music_interest],
        )
        user2 = User(
            telegram_id=67890,
            first_name="Мария",
            second_name="Петрова",
            faculty_id=f2.id,
            group_id=g2_1.id,
            interests=[travel_interest, music_interest],
        )
        db.add_all([user1, user2])
        db.commit()

        print("Данные успешно добавлены!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
