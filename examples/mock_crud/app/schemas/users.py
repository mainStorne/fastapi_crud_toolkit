import json
from datetime import datetime
from typing import Annotated, Literal, Any

from fastapi import UploadFile, File, Form
from fastapi_sqlalchemy_toolkit import make_partial_model
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from pydantic.main import IncEx


class BaseUser(BaseModel):
    """
    Это базовый класс для данных пользователя. Он содержит следующие поля:
    - username: Имя пользователя.
    - first_name: Имя пользователя.
    - middle_name: Отчество пользователя.
    - last_name: Фамилия пользователя.
    - email: Электронная почта пользователя.

    Метод __acl__ используется для определения списка контроля доступа для пользователя.
    """
    first_name: str
    middle_name: str | None = None
    last_name: str
    email: str
    about: str | None = None


class CreateUser(BaseUser):
    """
    Этот класс представляет данные, необходимые для создания нового пользователя. Он содержит следующие поля:
    - username: Имя пользователя.
    - first_name: Имя пользователя.
    - middle_name: Отчество пользователя.
    - last_name: Фамилия пользователя.
    - email: Электронная почта пользователя.
    - password: Пароль пользователя.
    """
    password: str
    username: str


class ReadUser(BaseUser):
    """
    Этот класс представляет данные, возвращаемые при чтении пользователя. Он содержит следующие поля:
    - id: Идентификатор пользователя.E
    - photo_url: URL фотографии пользователя.
    # is_superuser: Булево значение, указывающее, является ли пользователь суперпользователем.
    """
    id: int
    username: str
    photo_url: str | None
    is_superuser: bool
    is_verified: bool


_UpdateUser = make_partial_model(BaseUser)


class UpdateUser(_UpdateUser):
    photo_url: str | None = None

    @classmethod
    def as_form(cls,
                name: str = Form(),
                description: str = Form(),
                file: UploadFile | None = None,
                ):
        return cls(name=name, description=description)

    def model_dump(
            self,
            *,
            mode: Literal['json', 'python'] | str = 'python',
            include: IncEx | None = None,
            exclude: IncEx | None = None,
            context: Any | None = None,
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            round_trip: bool = False,
            warnings: bool | Literal['none', 'warn', 'error'] = True,
            serialize_as_any: bool = False,
    ) -> dict[str, Any]:
        return super().model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=True,
            round_trip=round_trip,
            warnings=warnings,
            serialize_as_any=serialize_as_any,
        )


class UserCredentials(BaseModel):
    """
    Этот класс представляет учетные данные, необходимые для аутентификации пользователя. Он содержит следующие поля:
    - login: Имя пользователя или электронная почта пользователя.
    - password: Пароль пользователя.
    """
    login: str
    password: str
