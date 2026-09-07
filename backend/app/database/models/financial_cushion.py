from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class CushionAnalysis(BaseModel):
    """Последний анализ PDF-выписки участника семьи.

    У каждого члена семьи своя выписка, поэтому запись привязана
    к пользователю (user_id — первичный ключ).
    """

    #: Идентификатор пользователя, загрузившего выписку.
    user_id: int
    #: Идентификатор семьи пользователя.
    family_id: int
    #: Число полных месяцев в расчёте.
    months_analyzed: int
    #: Итоговая сумма финансовой подушки (денормализация для рейтинга).
    cushion_total: Decimal = Decimal("0")
    #: Подписи полных месяцев (например, «июнь 2026»).
    full_months: List[str] = []
    #: Подписи отброшенных частичных месяцев.
    excluded_months: List[str] = []
    #: Полный JSON результата analyze_statement (транзакции, кандидаты).
    payload: Dict[str, Any] = {}
    #: Дата и время последнего обновления.
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "CushionAnalysis",
]
