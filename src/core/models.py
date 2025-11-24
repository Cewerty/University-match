"""
SQLAlchemy ORM models for users, interests, faculties, and groups.

This module defines the core database schema of the application, including:
- User: a Telegram user profile with relations to Faculty, Group, and Interests.
- Interest: a tag-like entity selected by users.
- Faculty and Group: organizational structure entities.
- user_interest_association: a many-to-many association table between users and interests.

Docstrings follow the Google style and are formatted to be compatible with ruff.
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

user_interest_association = Table(
    "user_interest_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("interest_id", Integer, ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    """
    User entity.

    Represents a Telegram user with personal data, academic affiliation, and selected interests.

    Attributes:
        tablename: Table name in the database (SQLAlchemy mapped).
        id: Primary key.
        telegram_id: Unique Telegram user identifier.
        first_name: User's first name.
        second_name: User's last name (family name).
        surname: Optional patronymic/middle name.
        phone_number: Contact phone number.
        interests: Many-to-many relationship to Interest.
        faculty_id: Foreign key to Faculty.
        group_id: Foreign key to Group.
        faculty: Relationship to Faculty (many users belong to one faculty).
        group: Relationship to Group (many users belong to one group).

    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    first_name = Column(String)
    second_name = Column(String)
    surname = Column(String, nullable=True)
    phone_number = Column(String)
    interests = relationship("Interest", secondary=user_interest_association, back_populates="users")
    faculty_id = Column(Integer, ForeignKey("faculties.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    faculty = relationship("Faculty", back_populates="users")
    group = relationship("Group", back_populates="users")

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the user."""
        return f"<User(name='{self.first_name} {self.second_name}')>"

    def __str__(self) -> str:
        """Return a human-readable full name of the user."""
        return f"{self.first_name} {self.second_name}"


class Interest(Base):
    """
    Interest entity.

    A tag-like value that can be selected by users. Connected to users through
    a many-to-many association.

    Attributes:
        tablename: Table name in the database.
        id: Primary key.
        name: Unique interest name.
        users: Back-populated relationship to User.

    """

    __tablename__ = "interests"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    users = relationship("User", secondary=user_interest_association, back_populates="interests")

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the interest."""
        return f"<Interest(name='{self.name}')>"

    def __str__(self) -> str:
        """Return the interest name."""
        return f"{self.name}"


class Faculty(Base):
    """
    Faculty entity.

    Represents a faculty that contains groups and users.

    Attributes:
        tablename: Table name in the database.
        id: Primary key.
        name: Unique faculty name.
        groups: Relationship to Group.
        users: Relationship to User.

    """

    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    groups = relationship("Group", back_populates="faculty")
    users = relationship("User", back_populates="faculty")

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the faculty."""
        return f"<Faculty(name='{self.name}')>"

    def __str__(self) -> str:
        """Return the faculty name."""
        return f"{self.name}"


class Group(Base):
    """
    Group entity.

    Represents an academic group belonging to a faculty.

    Attributes:
        tablename: Table name in the database.
        id: Primary key.
        name: Group name.
        faculty_id: Foreign key to Faculty.
        faculty: Relationship to Faculty.
        users: Relationship to User.

    """

    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    faculty_id = Column(Integer, ForeignKey("faculties.id"))
    faculty = relationship("Faculty", back_populates="groups")
    users = relationship("User", back_populates="group")

    def __repr__(self) -> str:
        """Return a debug-friendly representation of the group."""
        return f"<Group(name='{self.name}')>"

    def __str__(self) -> str:
        """Return the group name."""
        return f"{self.name}"
