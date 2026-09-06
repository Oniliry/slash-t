from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

#: Роль участника семьи: взрослый (платежеспособный) или ребёнок (неплатежеспособный).
UserRole = Literal["adult", "child"]


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
    #: Идентификатор семьи пользователя, если он уже присоединился к семье.
    family_id: Optional[int] = None
    #: Роль пользователя в семье (adult/child), если она уже выбрана.
    role: Optional[UserRole] = None
    #: Примерный месячный доход, указывается только взрослыми участниками.
    monthly_income: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "User",
]