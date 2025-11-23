import asyncio
from contextlib import asynccontextmanager
from typing import ClassVar

from fastapi import BackgroundTasks, FastAPI
from sqladmin import Admin, ModelView

from ..core import Faculty, Group, Interest, User, engine
from ..core.database import get_session
from ..services.matcher import matcher_service


async def refresh_index_task():
    async with get_session() as session:
        await matcher_service.update_index(session)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    print("Admin Panel Starting...")
    # Запускаем обновление индекса сразу при старте, но не ждем завершения (create_task)
    # Чтобы сервер запустился быстро и начал принимать запросы (хотя поиск пока выдаст 503)
    asyncio.create_task(refresh_index_task())
    yield
    # --- SHUTDOWN ---
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

admin = Admin(app, engine)


class UserAdmin(ModelView, model=User):
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
    column_list: ClassVar = [Interest.id, Interest.name]
    name = "Интерес"
    name_plural = "Интересы"
    icon = "fa-solid fa-star"

    column_searchable_list: ClassVar = [Interest.name]
    column_sortable_list: ClassVar = [Interest.name, Interest.id]


class FacultyAdmin(ModelView, model=Faculty):
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
def read_root():
    return {"message": "Перейдите на /admin для доступа к админ-панели"}


@app.post("/reindex")
async def force_reindex(background_tasks: BackgroundTasks):
    background_tasks.add_task(refresh_index_task)
    return {"status": "Index update started in background"}


@app.get("/search/{user_id}")
async def search_users(user_id: int):
    if not matcher_service.is_ready:
        return {"error": "System is warming up, please wait"}, 503

    results = await matcher_service.search(user_id)
    return {"results": results}
