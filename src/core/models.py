from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""

    pass


# Ассоциативная таблица для связи пользователей и интересов
users_interests = Table(
    "user_interests",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("interest_id", Integer, ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True),
)


class Faculty(Base):
    """Модель факультета."""

    __tablename__ = "faculties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    groups: Mapped[list["Group"]] = relationship("Group", back_populates="faculty")
    
    def __str__(self) -> str:
        """Output string for Faculty model."""
        return f"{self.name}"


class Group(Base):
    """Модель учебной группы."""

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    faculty_id: Mapped[int] = mapped_column(Integer, ForeignKey("faculties.id"))

    faculty: Mapped["Faculty"] = relationship("Faculty", back_populates="groups")
    users: Mapped[list["User"]] = relationship("User", back_populates="group")
    
    def __str__(self) -> str:
        """Output string for Group model."""
        return f"{self.name}"


class Interest(Base):
    """Модель интереса пользователя."""

    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship("User", secondary=users_interests, back_populates="interests")
    
    def __str__(self) -> str:
        """Output string for Interest model."""
        return f"{self.name}"


class User(Base):
    """Модель пользователя."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    second_name: Mapped[str] = mapped_column(String(100), nullable=False)
    surname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    faculty_id: Mapped[int] = mapped_column(Integer, ForeignKey("faculties.id"))
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"))

    faculty: Mapped["Faculty"] = relationship("Faculty")
    group: Mapped["Group"] = relationship("Group", back_populates="users")
    interests: Mapped[list["Interest"]] = relationship("Interest", secondary=users_interests, back_populates="users")
    
    def __str__(self) -> str:
        """Output string for User model."""
        return f"{self.second_name}, {self.first_name}, {self.surname}"