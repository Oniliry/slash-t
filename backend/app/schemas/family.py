from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from database.models.user import UserRole


class CreateFamilyRequest(BaseModel):
    """
    Схема запроса на создание семьи.

    :field name: Название семьи, придуманное создателем.
    """

    name: str = Field(min_length=1, max_length=150)


class JoinFamilyRequest(BaseModel):
    """
    Схема запроса на вход в существующую семью.

    :field invite_code: Код приглашения, полученный от создателя семьи.
    """

    invite_code: str = Field(min_length=4, max_length=12)


class SetRoleRequest(BaseModel):
    """
    Схема запроса на выбор роли пользователя в семье.

    :field role: Роль: adult (взрослый, платежеспособный) или child (ребёнок).
    :field monthly_income: Примерный месячный доход. Обязателен для взрослых,
        для детей игнорируется и всегда сохраняется как None.
    """

    role: UserRole
    monthly_income: Optional[Decimal] = Field(default=None, ge=0, le=100_000_000)

    @model_validator(mode="after")
    def validate_income_for_role(self) -> "SetRoleRequest":
        """Проверяет, что взрослый указал доход, а у ребёнка доход не сохраняется."""
        if self.role == "adult" and (self.monthly_income is None or self.monthly_income <= 0):
            raise ValueError("Взрослый участник должен указать примерный месячный доход.")

        if self.role == "child":
            self.monthly_income = None

        return self


class FamilyResponse(BaseModel):
    """
    Схема публичного ответа с данными семьи.

    :field id: Уникальный идентификатор семьи.
    :field name: Название семьи.
    :field invite_code: Код приглашения для других участников.
    :field created_by: Идентификатор создателя семьи.
    :field created_at: Дата и время создания семьи.
    """

    id: int
    name: str
    invite_code: str
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FamilyMemberResponse(BaseModel):
    """
    Схема данных участника семьи для списка участников.

    :field id: Уникальный идентификатор пользователя.
    :field name: Имя участника.
    :field role: Роль участника, если уже выбрана.
    :field monthly_income: Примерный месячный доход (только для взрослых).
    :field income_share: Доля участника в общем доходе семьи (0..1), если применимо.
    """

    id: int
    name: str
    role: Optional[UserRole] = None
    monthly_income: Optional[Decimal] = None
    income_share: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class FamilyStateResponse(BaseModel):
    """
    Схема ответа с полной информацией о семье текущего пользователя.

    :field family: Данные семьи.
    :field members: Список участников семьи с ролями и долями бюджета.
    """

    family: FamilyResponse
    members: List[FamilyMemberResponse]


__all__ = [
    "CreateFamilyRequest",
    "JoinFamilyRequest",
    "SetRoleRequest",
    "FamilyResponse",
    "FamilyMemberResponse",
    "FamilyStateResponse",
]
