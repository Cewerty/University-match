from typing import ClassVar

from fastapi import FastAPI
from sqladmin import Admin, ModelView

from ..core import Faculty, Group, Interest, User, engine

app = FastAPI()

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
