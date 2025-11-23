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
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    first_name = Column(String)
    second_name = Column(String)
    surname = Column(String, nullable=True)
    interests = relationship("Interest", secondary=user_interest_association, back_populates="users")
    faculty_id = Column(Integer, ForeignKey("faculties.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    faculty = relationship("Faculty", back_populates="users")
    group = relationship("Group", back_populates="users")

    def __repr__(self):
        return f"<User(name='{self.first_name} {self.second_name}')>"

    def __str__(self):
        return f"{self.first_name} {self.second_name}"


class Interest(Base):
    __tablename__ = "interests"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    users = relationship("User", secondary=user_interest_association, back_populates="interests")

    def __repr__(self):
        return f"<Interest(name='{self.name}')>"

    def __str__(self):
        return f"{self.name}"


class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    groups = relationship("Group", back_populates="faculty")
    users = relationship("User", back_populates="faculty")

    def __repr__(self) -> str:
        return f"<Faculty(name='{self.name}')>"

    def __str__(self) -> str:
        return f"{self.name}"


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    faculty_id = Column(Integer, ForeignKey("faculties.id"))
    faculty = relationship("Faculty", back_populates="groups")
    users = relationship("User", back_populates="group")

    def __repr__(self) -> str:
        return f"<Group(name='{self.name}')>"

    def __str__(self) -> str:
        return f"{self.name}"
