from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from database.models.cushion import CushionOperationKind


class CushionOperationResponse(BaseModel):
    """
    Одна операция с подушкой в ответе API.

    :field id: Идентификатор операции.
    :field kind: Тип операции: topup (пополнение) или withdraw (списание).
    :field amount: Сумма операции.
    :field comment: Комментарий.
    :field user_name: Имя участника, совершившего операцию.
    :field created_at: Дата и время операции.
    """

    id: int
    kind: CushionOperationKind
    amount: Decimal
    comment: Optional[str] = None
    user_name: Optional[str] = None
    created_at: datetime


class CushionGoalResponse(BaseModel):
    """
    Цель по финансовой подушке и прогресс её достижения.

    :field target_amount: Целевая сумма.
    :field months: На сколько месяцев расходов рассчитана подушка.
    :field progress_percent: Сколько процентов цели уже накоплено (0–100).
    """

    target_amount: Decimal
    months: int
    progress_percent: int = Field(ge=0, le=100)


class CushionStateResponse(BaseModel):
    """
    Полное состояние финансовой подушки семьи — для страницы «ФинПодушка».

    :field balance: Текущий размер подушки (пополнения минус списания).
    :field monthly_expenses: Средние расходы семьи в месяц за последние
        3 полных месяца — ориентир размера подушки.
    :field goal: Цель и прогресс, если цель установлена.
    :field operations: История операций, от новых к старым.
    """

    balance: Decimal
    monthly_expenses: Decimal
    goal: Optional[CushionGoalResponse] = None
    operations: List[CushionOperationResponse] = []


class CushionOperationRequest(BaseModel):
    """
    Запрос на пополнение или списание из подушки.

    :field amount: Сумма операции (положительная).
    :field comment: Комментарий, зачем операция.
    """

    amount: Decimal = Field(gt=0, le=100_000_000)
    comment: Optional[str] = Field(default=None, max_length=200)


class SetCushionGoalRequest(BaseModel):
    """
    Запрос на установку цели по подушке.

    :field target_amount: Целевая сумма.
    :field months: На сколько месяцев расходов рассчитана подушка.
    """

    target_amount: Decimal = Field(gt=0, le=1_000_000_000)
    months: int = Field(default=6, ge=1, le=60)


__all__ = [
    "CushionOperationResponse",
    "CushionGoalResponse",
    "CushionStateResponse",
    "CushionOperationRequest",
    "SetCushionGoalRequest",
]
