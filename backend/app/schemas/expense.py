from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from database.models.debt import DebtStatus
from database.models.expense import ExpenseCategory, ExpenseOwnerType


class CreateExpenseRequest(BaseModel):
    """
    Схема запроса на добавление покупки.

    :field amount: Сумма покупки.
    :field owner_type: Кому принадлежит покупка: self (себе), member
        (конкретному участнику семьи) или shared (общая, на всех).
    :field owner_id: Идентификатор участника-владельца. Обязателен только
        для owner_type="member", в остальных случаях игнорируется.
    :field category: Категория покупки. Если не указана, считается прочей.
    """

    amount: Decimal = Field(gt=0, le=100_000_000)
    owner_type: ExpenseOwnerType
    owner_id: Optional[int] = None
    category: ExpenseCategory = "other"

    @model_validator(mode="after")
    def validate_owner(self) -> "CreateExpenseRequest":
        """Проверяет, что для покупки конкретного участника указан его id."""
        if self.owner_type == "member" and self.owner_id is None:
            raise ValueError("Нужно выбрать участника семьи, которому принадлежит покупка.")

        if self.owner_type != "member":
            self.owner_id = None

        return self


class DebtParticipantResponse(BaseModel):
    """
    Краткие данные участника долга (для отображения имени в списке).

    :field id: Уникальный идентификатор пользователя.
    :field name: Имя участника.
    """

    id: int
    name: str


class DebtResponse(BaseModel):
    """
    Схема ответа с данными одного долга.

    :field id: Уникальный идентификатор долга.
    :field expense_id: Идентификатор покупки, из которой возник долг.
    :field amount: Сумма долга.
    :field status: Текущий статус долга.
    :field created_at: Дата и время возникновения долга.
    :field confirmed_at: Дата и время подтверждения погашения, если есть.
    :field debtor: Участник, который должен перевести деньги.
    :field creditor: Участник, которому причитается перевод.
    """

    id: int
    expense_id: int
    amount: Decimal
    status: DebtStatus
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    debtor: DebtParticipantResponse
    creditor: DebtParticipantResponse

    model_config = ConfigDict(from_attributes=True)


class ExpenseResponse(BaseModel):
    """
    Схема ответа с данными добавленной покупки и порождённых ею долгов.

    :field id: Уникальный идентификатор покупки.
    :field amount: Сумма покупки.
    :field owner_type: Кому принадлежит покупка.
    :field owner_id: Идентификатор участника-владельца, если применимо.
    :field payer_id: Идентификатор пользователя, который заплатил.
    :field category: Категория покупки.
    :field created_at: Дата и время добавления покупки.
    :field debts: Список долгов, созданных этой покупкой.
    """

    id: int
    amount: Decimal
    owner_type: ExpenseOwnerType
    owner_id: Optional[int] = None
    payer_id: int
    payer_name: Optional[str] = None
    category: ExpenseCategory = "other"
    created_at: datetime
    debts: List[DebtResponse] = []

    model_config = ConfigDict(from_attributes=True)


class MyDebtsResponse(BaseModel):
    """
    Схема ответа со сводкой долгов текущего пользователя.

    :field i_owe: Долги, которые должен перевести текущий пользователь.
    :field owed_to_me: Долги, которые причитаются текущему пользователю
        (подтвердить их погашение может только он).
    """

    i_owe: List[DebtResponse]
    owed_to_me: List[DebtResponse]


__all__ = [
    "CreateExpenseRequest",
    "DebtParticipantResponse",
    "DebtResponse",
    "ExpenseResponse",
    "MyDebtsResponse",
]
