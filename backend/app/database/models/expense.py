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
    #: Дата и время добавления покупки.
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "Expense",
    "ExpenseCategory",
    "ExpenseOwnerType",
]
