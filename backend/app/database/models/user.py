from datetime import datetime

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    """Модель пользователя без хранения пароля в объекте ответа."""

    #: Уникальный идентификатор пользователя.
    id: int
    #: Отображаемое имя пользователя.
    name: str
    #: Уникальный логин пользователя.
    login: str
    #: Дата и время регистрации пользователя.
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "User",
]