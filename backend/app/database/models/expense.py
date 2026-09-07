from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

#: Кому принадлежит покупка: себе (личный расход), конкретному участнику
#: семьи (тогда весь долг ложится на него) или общая (делится между всеми
#: остальными взрослыми пропорционально их доле бюджета).
ExpenseOwnerType = Literal["self", "member", "shared"]

#: Категория покупки. Проставляется пользователем при добавлении и может
#: быть скорректирована вручную позже.
ExpenseCategory = Literal[
    "groceries",
    "utilities",
    "transport",
    "cafe",
    "entertainment",
    "health",
    "clothing",
    "other",
]


class ExpenseItem(BaseModel):
    """Модель одной позиции покупки (товара из чека)."""

    #: Уникальный идентификатор позиции.
    id: int
    #: Идентификатор покупки, которой принадлежит позиция.
    expense_id: int
    #: Название товара.
    name: str
    #: Стоимость позиции целиком.
    sum: Decimal
    #: Категория позиции.
    category: ExpenseCategory = "other"
    #: Кому принадлежит именно этот товар (личное/общее у каждой позиции своё).
    owner_type: ExpenseOwnerType = "shared"
    #: Идентификатор участника-владельца товара (только для owner_type="member").
    owner_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class Expense(BaseModel):
    """Модель покупки, добавленной участником семьи."""

    #: Уникальный идентификатор покупки.
    id: int
    #: Идентификатор семьи, в рамках которой добавлена покупка.
    family_id: int
    #: Идентификатор пользователя, который фактически заплатил.
    payer_id: int
    #: Сумма покупки.
    amount: Decimal
    #: Кому принадлежит покупка.
    owner_type: ExpenseOwnerType
    #: Идентификатор участника-владельца покупки (только для owner_type="member").
    owner_id: Optional[int] = None
    #: Категория покупки.
    category: ExpenseCategory = "other"
    #: Название покупки (например, магазин с чека), если указано.
    shop_name: Optional[str] = None
    #: Дата и время добавления покупки.
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "Expense",
    "ExpenseCategory",
    "ExpenseItem",
    "ExpenseOwnerType",
]
