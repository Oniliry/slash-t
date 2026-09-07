"""DTO анализа PDF-выписки — зеркала моделей готового пакета financial_cushion."""

from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class StatementTxDTO(BaseModel):
    """Транзакция выписки, редактируемая пользователем (round-trip JSON)."""

    #: Уникальный ID транзакции (uuid4 hex).
    tx_id: str
    #: Дата операции, YYYY-MM-DD.
    date: str
    #: Категория, определённая алгоритмом.
    group: str
    #: Мерчант / ФИО контрагента.
    counterparty: str
    #: Сумма списания, руб.
    amount: float = Field(gt=0)
    #: Регулярная ли трата по мнению алгоритма.
    is_regular: bool = False
    #: Учитывать ли трату в пересчёте (пользователь может выключить).
    is_active: bool = True
    #: True — регулярный p2p-перевод (кандидат в услуги).
    is_transfer: bool = False
    #: Пользовательская категория услуги для перевода.
    transfer_label: Optional[str] = None
    #: Для переводов: включать ли в подушку.
    include_in_cushion: bool = False


class TransferCandidateDTO(BaseModel):
    """Подсказка UI: регулярный перевод, требующий решения."""

    #: ФИО / счёт получателя перевода.
    counterparty: str
    #: Сумма одного перевода, руб.
    amount: float
    #: Сколько раз повторялся.
    occurrences: int


class StatementAnalysisResponse(BaseModel):
    """Ответ загрузки выписки — пользователь правит его и отправляет назад."""

    #: Полные месяцы периода (например, «июнь 2026»).
    full_months: List[str]
    #: Отброшенные частичные месяцы.
    excluded_months: List[str]
    #: Число полных месяцев (знаменатель формулы).
    months_analyzed: int = Field(ge=1)
    #: Транзакции списаний за полные месяцы.
    transactions: List[StatementTxDTO]
    #: Регулярные переводы-кандидаты в «скрытые подписки».
    transfer_candidates: List[TransferCandidateDTO] = []


class StatementRecalculateRequest(BaseModel):
    """Изменённый пользователем JSON для пересчёта подушки."""

    #: Число полных месяцев (можно не слать, если есть full_months).
    months_analyzed: Optional[int] = Field(default=None, ge=1)
    #: Подписи полных месяцев.
    full_months: List[str] = []
    #: Отброшенные частичные месяцы.
    excluded_months: List[str] = []
    #: Транзакции с флагами пользователя.
    transactions: List[StatementTxDTO]

    @model_validator(mode="after")
    def _check_denominator(self) -> "StatementRecalculateRequest":
        if self.months_analyzed is None and not self.full_months:
            raise ValueError(
                "Нужен months_analyzed либо непустой full_months "
                "(знаменатель формулы пересчёта)"
            )
        return self


class StatementGroupDTO(BaseModel):
    """Итог по одной группе расходов."""

    #: Название категории.
    name: str
    #: Среднее в месяц, руб.
    monthly_amount: float
    #: Число операций в месяц (в среднем).
    ops_count: int
    #: Всего потрачено за все полные месяцы, руб.
    total_amount: float = 0.0
    #: Пояснение, что входит в группу.
    description: str = ""
    #: Список операций «контрагент — сумма» (по убыванию суммы).
    operations: List[str] = []


class StatementRecalculateResponse(BaseModel):
    """Результат пересчёта подушки по правкам пользователя."""

    #: Число полных месяцев (знаменатель).
    months_analyzed: int
    #: Итоговая сумма подушки: [активные траты] / [полные месяцы].
    cushion_total: float
    #: Категории, включённые в подушку (по убыванию суммы).
    groups: List[StatementGroupDTO]
    #: Категории вне подушки (исключены пользователем / нерегулярные).
    excluded_groups: List[StatementGroupDTO]


class FamilyCushionRatingItem(BaseModel):
    """Строка рейтинга семьи: финподушка одного участника."""

    #: Идентификатор пользователя.
    user_id: int
    #: Имя участника.
    user_name: str
    #: Итог его финподушки (0, если выписка не загружалась).
    cushion_total: float
    #: Число полных месяцев в его расчёте.
    months_analyzed: Optional[int] = None


__all__ = [
    "StatementTxDTO",
    "TransferCandidateDTO",
    "StatementAnalysisResponse",
    "StatementRecalculateRequest",
    "StatementGroupDTO",
    "StatementRecalculateResponse",
    "FamilyCushionRatingItem",
]
