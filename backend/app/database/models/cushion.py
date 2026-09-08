from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

#: Тип операции с подушкой: пополнение (topup) или списание (withdraw).
CushionOperationKind = Literal["topup", "withdraw"]


class CushionOperation(BaseModel):
    """Операция пополнения или списания из финансовой подушки семьи."""

    #: Уникальный идентификатор операции.
    id: int
    #: Идентификатор семьи.
    family_id: int
    #: Идентификатор пользователя, совершившего операцию.
    user_id: int
    #: Тип операции: topup (пополнение) или withdraw (списание).
    kind: CushionOperationKind
    #: Сумма операции (всегда положительная).
    amount: Decimal
    #: Комментарий, зачем пополнили или на что списали.
    comment: Optional[str] = None
    #: Дата и время операции.
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CushionGoal(BaseModel):
    """Цель по финансовой подушке семьи (например, 6 месяцев расходов)."""

    #: Идентификатор семьи, к которой привязана цель.
    family_id: int
    #: Целевая сумма подушки.
    target_amount: Decimal
    #: На сколько месяцев расходов рассчитана подушка.
    months: int = 6
    #: Дата и время последнего обновления цели.
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "CushionOperation",
    "CushionOperationKind",
    "CushionGoal",
]
