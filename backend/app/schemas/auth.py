from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from database.models.user import UserRole


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
    #: Идентификатор семьи, если пользователь уже присоединился к ней.
    family_id: Optional[int] = None
    #: Роль пользователя в семье, если она уже выбрана.
    role: Optional[UserRole] = None
    #: Примерный месячный доход, указывается только взрослыми участниками.
    monthly_income: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """
    Схема ответа при входе/регистрации: данные пользователя и токен сессии.

    :field user: Публичные данные пользователя.
    :field access_token: JWT-токен текущей сессии. Хранится на фронтенде
        в sessionStorage (в рамках одной вкладки браузера), а не в cookie —
        это нужно, чтобы вход в аккаунт в одной вкладке не сбрасывал сессию
        в другой открытой вкладке того же сайта.
    """

    user: UserResponse
    access_token: str


__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "AuthResponse",
]