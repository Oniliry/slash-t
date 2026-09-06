from decimal import Decimal

from pydantic import BaseModel, Field


class UpdateNameRequest(BaseModel):
    """
    Схема запроса на смену отображаемого имени.

    :field name: Новое имя, которое увидят остальные участники семьи.
    """

    name: str = Field(min_length=1, max_length=100)


class UpdateIncomeRequest(BaseModel):
    """
    Схема запроса на изменение примерного месячного дохода.

    :field monthly_income: Новый доход. Доступно только пользователям с ролью adult.
    """

    monthly_income: Decimal = Field(gt=0, le=100_000_000)


class ChangePasswordRequest(BaseModel):
    """
    Схема запроса на смену пароля.

    :field current_password: Текущий пароль — для подтверждения личности.
    :field new_password: Новый пароль.
    """

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=128)


__all__ = [
    "UpdateNameRequest",
    "UpdateIncomeRequest",
    "ChangePasswordRequest",
]
