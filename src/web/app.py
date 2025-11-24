"""
Admin panel and API module for user matching service.

This module provides FastAPI application with SQLAdmin interface for data management
and REST API endpoints for user matching functionality.
"""

import asyncio
from collections.abc import Generator
from contextlib import asynccontextmanager
from typing import Any, ClassVar

from fastapi import BackgroundTasks, FastAPI
from sqladmin import Admin, ModelView

from ..core import Faculty, Group, Interest, User, engine
from ..core.database import get_session
from ..services.matcher import matcher_service


async def refresh_index_task() -> None:
    """
    Background task to refresh the user matching index.

    Fetches current user data from database and updates the FAISS index
    for similarity search.
    """
    async with get_session() as session:
        await matcher_service.update_index(session)


@asynccontextmanager
async def lifespan(app: FastAPI) -> Generator[None, Any, None]:
    """
    Lifespan context manager for FastAPI application.

    Handles startup and shutdown events for the application.

    Args:
        app: FastAPI application instance.

    Yields:
        None: Application runs until shutdown.

    """
    # --- STARTUP ---
    print("Admin Panel Starting...")
    asyncio.create_task(refresh_index_task())  # noqa: RUF006
    yield
    # --- SHUTDOWN ---
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

admin = Admin(app, engine)


class UserAdmin(ModelView, model=User):
    """
    Admin interface for User model.

    Attributes:
        column_list: Columns to display in list view.
        name: Singular model name.
        name_plural: Plural model name.
        icon: FontAwesome icon class.
        column_searchable_list: Searchable columns.
        column_sortable_list: Sortable columns.
        column_formatters: Custom column formatters.

    """

    column_list: ClassVar = [User.id, User.telegram_id, User.first_name, User.second_name, User.faculty, User.group]
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"

    column_searchable_list: ClassVar = [User.first_name, User.second_name]
    column_sortable_list: ClassVar = [User.id]

    column_formatters: ClassVar = {
        User.faculty: lambda m, a: m.faculty.name + "❤️" if m.faculty.name == "ФБ" else m.faculty.name,
    }


class InterestAdmin(ModelView, model=Interest):
    """
    Admin interface for Interest model.

    Attributes:
        column_list: Columns to display in list view.
        name: Singular model name.
        name_plural: Plural model name.
        icon: FontAwesome icon class.
        column_searchable_list: Searchable columns.
        column_sortable_list: Sortable columns.

    """

    column_list: ClassVar = [Interest.id, Interest.name]
    name = "Интерес"
    name_plural = "Интересы"
    icon = "fa-solid fa-star"

    column_searchable_list: ClassVar = [Interest.name]
    column_sortable_list: ClassVar = [Interest.name, Interest.id]


class FacultyAdmin(ModelView, model=Faculty):
    """
    Admin interface for Faculty model.

    Attributes:
        column_list: Columns to display in list view.
        name: Singular model name.
        name_plural: Plural model name.
        icon: FontAwesome icon class.
        column_searchable_list: Searchable columns.
        column_sortable_list: Sortable columns.
        column_formatters: Custom column formatters.

    """

    column_list: ClassVar = [Faculty.id, Faculty.name]
    name = "Факультет"
    name_plural = "Факультеты"
    icon = "fa-solid fa-building-columns"

    column_formatters: ClassVar = {
        Faculty.name: lambda m, a: m.name + "❤️" if m.name == "ФБ" else m.name,
    }

    column_searchable_list: ClassVar = [Faculty.name]
    column_sortable_list: ClassVar = [Faculty.name, Faculty.id]


class GroupAdmin(ModelView, model=Group):
    """
    Admin interface for Group model.

    Attributes:
        column_list: Columns to display in list view.
        name: Singular model name.
        name_plural: Plural model name.
        icon: FontAwesome icon class.
        column_searchable_list: Searchable columns.
        column_sortable_list: Sortable columns.
        column_formatters: Custom column formatters.

    """

    column_list: ClassVar = [Group.id, Group.name, Group.faculty]
    name = "Группа"
    name_plural = "Группы"
    icon = "fa-solid fa-users"

    column_formatters: ClassVar = {
        Group.faculty: lambda m, a: m.faculty.name + "❤️" if m.faculty.name == "ФБ" else m.faculty.name,
    }

    column_sortable_list: ClassVar = [Group.name, Group.id]
    column_searchable_list: ClassVar = [Group.name]


admin.add_view(UserAdmin)
admin.add_view(InterestAdmin)
admin.add_view(FacultyAdmin)
admin.add_view(GroupAdmin)


@app.get("/")
def read_root() -> dict[str, str]:
    """
    Root endpoint redirecting to admin panel.

    Returns:
        Dictionary with welcome message and admin panel instructions.

    """
    return {"message": "Перейдите на /admin для доступа к админ-панели"}


@app.post("/reindex")
async def force_reindex(background_tasks: BackgroundTasks) -> dict[str, str]:
    """
    Force reindexing of user matching service.

    Args:
        background_tasks: FastAPI background tasks for async processing.

    Returns:
        Dictionary with status message indicating index update started.

    """
    background_tasks.add_task(refresh_index_task)
    return {"status": "Index update started in background"}


@app.get("/search/{user_id}")
async def search_users(user_id: int) -> dict:
    """
    Search for user matches based on interests similarity.

    Args:
        user_id: ID of the user to find matches for.

    Returns:
        Dictionary with search results or error message.

    Raises:
        503: If matching service is not ready yet.

    """
    if not matcher_service.is_ready:
        return {"error": "System is warming up, please wait"}, 503

    results = await matcher_service.search(user_id)
    return {"results": results}
