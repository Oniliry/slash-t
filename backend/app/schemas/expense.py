from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from database.models.debt import DebtStatus
from database.models.expense import ExpenseCategory, ExpenseOwnerType


class ExpenseItemInput(BaseModel):
    """
    Схема одной позиции покупки при создании (например, товара с чека).

    :field name: Название товара.
    :field sum: Стоимость позиции целиком.
    :field category: Категория позиции.
    :field owner_type: Кому принадлежит именно этот товар — self/member/shared.
        Позволяет в одном чеке пометить часть товаров личными (алкоголь,
        косметика, техника), а часть — общими.
    :field owner_id: Идентификатор участника-владельца товара. Обязателен
        только для owner_type="member".
    """

    name: str = Field(min_length=1, max_length=200)
    sum: Decimal = Field(gt=0, le=100_000_000)
    category: ExpenseCategory = "other"
    owner_type: ExpenseOwnerType = "shared"
    owner_id: Optional[int] = None


class CreateExpenseRequest(BaseModel):
    """
    Схема запроса на добавление покупки.

    :field amount: Сумма покупки. Если передан список items, сумма
        считается автоматически как сумма позиций, поле игнорируется.
    :field owner_type: Кому принадлежит покупка: self (себе), member
        (конкретному участнику семьи) или shared (общая, на всех).
    :field owner_id: Идентификатор участника-владельца. Обязателен только
        для owner_type="member", в остальных случаях игнорируется.
    :field category: Категория покупки. Если не указана, считается прочей.
    :field shop_name: Название покупки (например, магазин с чека).
    :field items: Список позиций покупки (товаров с чека), если покупка
        добавлена через распознавание чека.
    """

    amount: Optional[Decimal] = Field(default=None, gt=0, le=100_000_000)
    owner_type: ExpenseOwnerType = "shared"
    owner_id: Optional[int] = None
    category: ExpenseCategory = "other"
    shop_name: Optional[str] = Field(default=None, max_length=150)
    items: Optional[List[ExpenseItemInput]] = None

    @model_validator(mode="after")
    def validate_owner(self) -> "CreateExpenseRequest":
        """Проверяет владельца покупки — либо один на весь чек, либо у каждого товара свой."""
        if self.items:
            # Покупка через чек: у каждого товара свой владелец, поэтому
            # верхнеуровневый owner_type не обязателен и не проверяется строго.
            for item in self.items:
                if item.owner_type == "member" and item.owner_id is None:
                    raise ValueError(
                        f"Нужно выбрать участника семьи, которому принадлежит товар «{item.name}».",
                    )
                if item.owner_type != "member":
                    item.owner_id = None

            self.amount = sum((item.sum for item in self.items), Decimal("0"))
            self.owner_id = None
            return self

        if self.owner_type == "member" and self.owner_id is None:
            raise ValueError("Нужно выбрать участника семьи, которому принадлежит покупка.")

        if self.owner_type != "member":
            self.owner_id = None

        if self.amount is None:
            raise ValueError("Нужно указать сумму покупки.")

        return self


class ExpenseItemResponse(BaseModel):
    """
    Схема ответа с данными одной позиции покупки.

    :field id: Уникальный идентификатор позиции.
    :field name: Название товара.
    :field sum: Стоимость позиции целиком.
    :field category: Категория позиции.
    :field owner_type: Кому принадлежит этот товар — self/member/shared.
    :field owner_id: Идентификатор участника-владельца товара, если применимо.
    :field owner_name: Имя владельца товара для отображения (None для общих).
    """

    id: int
    name: str
    sum: Decimal
    category: ExpenseCategory = "other"
    owner_type: ExpenseOwnerType = "shared"
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


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
    :field shop_name: Название покупки (например, магазин с чека), если есть.
    :field items_count: Количество позиций в покупке (0, если добавлена вручную).
    :field created_at: Дата и время добавления покупки.
    :field debts: Список долгов, созданных этой покупкой.
    :field items: Позиции покупки — заполняется только в ответе на детальный запрос.
    """

    id: int
    amount: Decimal
    owner_type: ExpenseOwnerType
    owner_id: Optional[int] = None
    payer_id: int
    payer_name: Optional[str] = None
    category: ExpenseCategory = "other"
    shop_name: Optional[str] = None
    items_count: int = 0
    created_at: datetime
    debts: List[DebtResponse] = []
    items: List[ExpenseItemResponse] = []

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
    "ExpenseItemInput",
    "ExpenseItemResponse",
    "ExpenseResponse",
    "MyDebtsResponse",
]
