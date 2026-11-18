"""
Shared test setup.

Settings are read from the environment when src.core.config is imported, so
test values are set here, before any project module is imported. Tests never
touch a real database file or download an embedding model.
"""

import os

os.environ.update(
    {
        "BOT_TOKEN": "123456:TEST-TOKEN-NOT-REAL-AAAAAAAAAAAAAAAA",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "REDIS_URL": "",
        "TELEGRAM_PROXY_URL": "",
        "LOG_LEVEL": "CRITICAL",
    }
)

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.models import Base, Faculty, Group, Interest


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Fresh in-memory SQLite database with all tables, one per test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as db:
        yield db
    await engine.dispose()


@pytest.fixture
async def catalog(session: AsyncSession) -> dict[str, object]:
    """One faculty, one group and a few interests."""
    faculty = Faculty(name="ФБ")
    group = Group(name="ФБ-101", faculty=faculty)
    interests = {name: Interest(name=name) for name in ["a", "b", "c"]}
    session.add_all([faculty, group, *interests.values()])
    await session.commit()
    return {"faculty": faculty, "group": group, "interests": interests}
