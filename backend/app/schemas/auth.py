from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequest(BaseModel):
    """
    Схема запроса на регистрацию пользователя.

    :field name: Имя пользователя.
    :field login: Уникальный логин длиной от 3 до 50 символов.
    :field password: Пароль длиной от 8 до 128 символов.
    """

    name: str = Field(min_length=1, max_length=100)
    login: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    """
    Схема запроса на вход пользователя.

    :field login: Логин пользователя.
    :field password: Пароль пользователя.
    """

    login: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    """
    Схема публичного ответа с данными пользователя.

    :field id: Уникальный идентификатор пользователя.
    :field name: Имя пользователя.
    :field login: Логин пользователя.
    :field created_at: Дата и время регистрации.
    """

    id: int
    name: str
    login: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
]