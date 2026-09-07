"""Расчёт финансовой подушки (необходимого минимума расходов) на месяц.

Алгоритм:
  1. Из PDF-выписки извлекаются операции и фильтруются только списания.
  2. Определяются ПОЛНЫЕ месяцы периода (determine_full_months):
     частичные крайние месяцы (например, выписка сформирована 4-м числом)
     полностью исключаются из расчёта, чтобы не занижать средние.
     Все средние считаются как:
         [сумма трат за ПОЛНЫЕ месяцы] / [количество ПОЛНЫХ месяцев].
  3. Каждая операция относится к канонической группе расходов
     (categories.classify).
  4. Для каждой группы считается помесячная сумма и число операций;
     группа включается в подушку, если встречалась не менее чем в
     ``min_month_share`` доле ПОЛНЫХ месяцев (регулярность).
  5. Отдельный контур — «скрытые подписки» в переводах (см.
     find_regular_transfers): регулярные переводы одному контрагенту
     с примерно равными суммами. Они изолируются и показываются
     пользователю на подтверждение (JSON-флаг / интерактив / API).
  6. Подушка = сумма оценочных помесячных расходов регулярных групп
     (mean/median/min — по настройке) + подтверждённые регулярные
     переводы.

Двухэтапный сценарий (интерактивное редактирование пользователем):
  - analyze_statement() — шаг 1: PDF -> редактируемый JSON транзакций
    (TxRecord, у каждой uuid и флаги is_active/include_in_cushion);
  - recalculate() — шаг 2: пересчёт по изменённому пользователем набору
    по формуле [сумма активных трат] / [число полных месяцев].

Категории в итоговом отчёте сортируются по убыванию суммы.
"""
from __future__ import annotations

import json
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import pandas as pd

from .categories import TRANSIT_CATEGORIES, classify, description_for_group
from .parser import Operation, StatementMeta, parse_statement_detailed

TRANSFERS_GROUP = "Переводы"
CASH_GROUP = "Наличные (снятие)"

# Стратегии оценки «минимально необходимой» суммы группы за месяц.
# mean — формула ТЗ: сумма за полные месяцы / число полных месяцев.
STRATEGIES = ("mean", "median", "min")

# Пороги «полноты» крайних месяцев
FIRST_MONTH_MAX_DAY = 5    # первая транзакция месяца не позднее 5 числа...
LAST_MONTH_MIN_DAY = 25    # ...либо дата формирования >= 25 числа...
MIN_MONTH_SPAN_DAYS = 25   # ...либо >= 25 дней между первой и последней транзакцией месяца

MONTH_NAMES_RU = {
    1: "январь", 2: "февраль", 3: "март", 4: "апрель",
    5: "май", 6: "июнь", 7: "июль", 8: "август",
    9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь",
}


def _month_label(period: pd.Period) -> str:
    """2026-06 -> 'июнь 2026'."""
    return f"{MONTH_NAMES_RU[period.month]} {period.year}"


@dataclass
class GroupResult:
    """Итог по одной группе расходов."""

    name: str
    monthly_amount: float   # оценочная сумма на следующий месяц
    ops_count: int          # среднее число операций в месяц
    description: str        # пояснение, что входит в группу
    included: bool          # включена ли в подушку
    operations: List[str] = field(default_factory=list)  # «операция — сумма»


@dataclass
class TransferCandidate:
    """Регулярный перевод, требующий решения пользователя."""

    counterparty: str       # ФИО / счёт получателя перевода
    amount: float           # медианная сумма перевода за месяц
    occurrences: int        # сколько месяцев повторялся
    label: Optional[str] = None     # пользовательское название услуги
    include: Optional[bool] = None  # включать ли в подушку (решение)


@dataclass
class CushionResult:
    """Полный результат расчёта."""

    period_start: str
    period_end: str
    months_analyzed: int
    cushion_total: float
    full_months: List[str] = field(default_factory=list)
    excluded_months: List[str] = field(default_factory=list)
    groups: List[GroupResult] = field(default_factory=list)
    candidates: List[TransferCandidate] = field(default_factory=list)
    excluded_groups: List[GroupResult] = field(default_factory=list)

    @property
    def pending_candidates(self) -> List[TransferCandidate]:
        return [c for c in self.candidates if c.include is None]


def fmt_money(value: float) -> str:
    """1234567.8 -> '1 234 567,80' (формат для отчётов)."""
    whole = int(round(value * 100)) // 100
    cents = int(round((value - whole) * 100))
    return f"{whole:,}".replace(",", " ") + f",{cents:02d}"


def _shorten(name: str, limit: int = 40) -> str:
    """Короткое имя операции для отчёта."""
    name = " ".join(str(name).split())
    return name if len(name) <= limit else name[: limit - 1] + "…"


def operations_to_frame(operations: Sequence[Operation]) -> pd.DataFrame:
    """Список Operation -> DataFrame с нормализованными группами."""
    rows = [
        {
            "date": op.date,
            "month": pd.Timestamp(op.date).to_period("M"),
            "category_raw": op.category,
            "description": op.description,
            "counterparty": op.counterparty,
            "amount": op.amount,
            "is_income": op.is_income,
        }
        for op in operations
    ]
    df = pd.DataFrame(rows)
    if df.empty:
        return df.assign(group=pd.Series(dtype=str))
    df["group"] = [
        classify(row.category_raw, row.description) for row in df.itertuples()
    ]
    return df


def _month_range(df: pd.DataFrame) -> List[pd.Period]:
    """Все календарные месяцы между первой и последней операцией."""
    if df.empty:
        return []
    return list(pd.period_range(df["month"].min(), df["month"].max(), freq="M"))


def determine_full_months(
    expenses: pd.DataFrame,
    formation_date: Optional[datetime] = None,
) -> Tuple[List[pd.Period], List[pd.Period]]:
    """Определяет, какие месяцы периода считаются «полными».

    Правила:
      - ПОСЛЕДНИЙ месяц полон, только если дата формирования выписки
        (или дата последней операции, если первая не извлеклась)
        наступила не ранее 25-го числа этого месяца. Иначе месяц
        частичный (например, выписка до 04.09) и полностью исключается.
      - ПЕРВЫЙ месяц полон, если первая транзакция совершена не позднее
        5-го числа ИЛИ между первой и последней транзакцией этого месяца
        прошло не менее 25 дней.
      - Промежуточные месяцы считаются полными всегда.
      - Если месяц одновременно первый и последний (весь период в одном
        месяце), применяются оба правила.

    Returns:
        (список полных месяцев, список исключённых частичных месяцев).
    """
    all_months = _month_range(expenses)
    if not all_months:
        return [], []

    # Опорная дата для проверки последнего месяца: дата формирования
    # выписки, а при её отсутствии — дата последней операции.
    cutoff = (
        pd.Timestamp(formation_date)
        if formation_date is not None
        else pd.Timestamp(expenses["date"].max())
    )

    full: List[pd.Period] = []
    excluded: List[pd.Period] = []
    n = len(all_months)
    for i, month in enumerate(all_months):
        dates = pd.to_datetime(
            expenses.loc[expenses["month"] == month, "date"].sort_values()
        )
        is_first, is_last = i == 0, i == n - 1
        is_full = True

        if is_first and n > 1:
            first_day = int(dates.iloc[0].day) if not dates.empty else 99
            span = (
                int((dates.iloc[-1] - dates.iloc[0]).days) if len(dates) >= 2 else 0
            )
            is_full = (
                first_day <= FIRST_MONTH_MAX_DAY or span >= MIN_MONTH_SPAN_DAYS
            )

        if is_last:
            # месяц полон, если опорная дата наступила не ранее 25-го
            # числа этого месяца (или позже — в следующем месяце)
            threshold = pd.Timestamp(year=month.year, month=month.month, day=LAST_MONTH_MIN_DAY)
            is_full = is_full and cutoff >= threshold

        (full if is_full else excluded).append(month)
    return full, excluded


def find_regular_transfers(
    expenses: pd.DataFrame,
    months: Sequence[pd.Period],
    min_month_share: float = 0.5,
    amount_tolerance: float = 0.10,
    min_occurrences: int = 2,
) -> List[TransferCandidate]:
    """Поиск «скрытых подписок» среди переводов.

    Перевод контрагенту считается регулярным, если:
      - он повторялся не менее ``min_occurrences`` раз и не менее чем в
        ``min_month_share`` доле месяцев периода (т.е. практически
        каждый месяц);
      - суммы переводов примерно одинаковы: максимальное отклонение
        помесячной суммы от медианы не превышает ``amount_tolerance``
        (5–10% по умолчанию).

    Именно так алгоритм находит переводы ОДНОМУ И ТОМУ ЖЕ получателю
    (совпадение ФИО в «Перевод для ...») — частные услуги: аренда,
    репетитор, перевод за ЖКХ и т.п., которые не видны в категориях
    Сбера и потому легко теряются в общей массе переводов.
    """
    transfers = expenses[expenses["group"] == TRANSFERS_GROUP]
    candidates: List[TransferCandidate] = []
    if transfers.empty or not len(months):
        return candidates

    min_months = max(min_occurrences, math.ceil(min_month_share * len(months)))
    for counterparty, grp in transfers.groupby("counterparty"):
        monthly = grp.groupby("month")["amount"].sum()
        if len(monthly) < min_months:
            continue
        median = float(monthly.median())
        if median <= 0:
            continue
        max_dev = float((monthly - median).abs().max()) / median
        if max_dev > amount_tolerance:
            continue
        candidates.append(
            TransferCandidate(
                counterparty=str(counterparty),
                amount=round(median, 2),
                occurrences=int(len(monthly)),
            )
        )
    candidates.sort(key=lambda c: -c.amount)
    return candidates


def load_decisions(source: Union[str, Path, dict, None]) -> Dict[str, dict]:
    """Загружает решения по переводам из JSON-файла либо словаря.

    Формат JSON:
        {
          "И. Иван Иванович": {"label": "Репетитор", "include": true},
          "Г. Санан Джафар Оглы": {"include": false}
        }
    """
    if source is None:
        return {}
    if isinstance(source, dict):
        return source
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    return {str(k): v for k, v in data.items()}


def apply_decisions(
    candidates: List[TransferCandidate],
    decisions: Dict[str, dict],
) -> List[TransferCandidate]:
    """Применяет пользовательские решения (JSON-флаг / API) к кандидатам.

    Совпадение контрагента — по нормализованной строке (регистр и
    лишние пробелы не важны). Неразрешённые кандидаты попадают в
    интерактивный блок отчёта.
    """
    normalized = {
        " ".join(k.lower().split()): v
        for k, v in decisions.items()
        if isinstance(v, dict)
    }
    for cand in candidates:
        key = " ".join(cand.counterparty.lower().split())
        decision = normalized.get(key)
        if not decision:
            continue
        cand.include = bool(decision.get("include"))
        cand.label = decision.get("label") or cand.label
    return candidates


def prompt_decisions_interactive(candidates: List[TransferCandidate]) -> None:
    """Интерактивный CLI-запрос по каждому неразрешённому переводу."""
    for cand in candidates:
        print(
            f"\nВнимание! Обнаружен регулярный перевод контрагенту "
            f"«{cand.counterparty}» на сумму ~{cand.amount:,.2f} руб., "
            f"повторялся {cand.occurrences} раз(а)."
        )
        label = input("  Как обозначить эту услугу (Enter — оставить как есть): ").strip()
        answer = input("  Включать ли её в финансовую подушку? [y/N]: ").strip().lower()
        if label:
            cand.label = label
        cand.include = answer in {"y", "yes", "д", "да"}


def _aggregate_groups(
    expenses: pd.DataFrame,
    months: Sequence[pd.Period],
    strategy: str,
    min_month_share: float,
) -> List[GroupResult]:
    """Агрегация по группам ТОЛЬКО за полные месяцы.

    Оценка на следующий месяц:
      mean   = сумма трат за полные месяцы / число полных месяцев (ТЗ);
      median = медиана помесячных сумм (устойчива к выбросам);
      min    = минимальная помесячная сумма.
    Число операций — в среднем за полный месяц.
    """
    results: List[GroupResult] = []
    n_months = len(months)
    min_months = max(1, math.ceil(min_month_share * n_months))

    for group, grp in expenses.groupby("group"):
        group = str(group)
        monthly = grp.groupby("month")["amount"].sum().reindex(months, fill_value=0.0)
        months_present = int((monthly > 0).sum())
        if strategy == "median":
            base = float(monthly[monthly > 0].median()) if months_present else 0.0
        elif strategy == "min":
            base = float(monthly.min())
        else:  # mean
            base = float(monthly.sum() / n_months) if n_months else 0.0

        avg_ops = math.ceil(len(grp) / n_months) if n_months else 0
        sorted_ops = grp.sort_values("amount", ascending=False)
        operations = [
            f"{_shorten(name)} — {fmt_money(amount)} руб."
            for name, amount in zip(sorted_ops["counterparty"], sorted_ops["amount"])
        ]
        included = months_present >= min_months and group not in TRANSIT_CATEGORIES
        results.append(
            GroupResult(
                name=group,
                monthly_amount=round(base, 2),
                ops_count=avg_ops,
                description=description_for_group(group),
                included=included,
                operations=operations,
            )
        )
    return results


def calculate_cushion(
    source: Union[str, bytes, Path],
    decisions: Union[str, Path, dict, None] = None,
    strategy: str = "mean",
    min_month_share: float = 0.5,
    amount_tolerance: float = 0.10,
) -> CushionResult:
    """Главная функция сервиса: PDF-выписка -> финансовая подушка.

    Args:
        source: путь к PDF или содержимое файла (bytes) — например,
            из FastAPI UploadFile.
        decisions: JSON-файл/словарь решений по регулярным переводам.
        strategy: mean | median | min — как считать сумму группы
            (по умолчанию mean: сумма за полные месяцы / число полных
            месяцев).
        min_month_share: доля ПОЛНЫХ месяцев, в которых должна
            встречаться группа/перевод, чтобы считаться регулярной.
        amount_tolerance: допустимый разброс сумм регулярных переводов.

    Returns:
        CushionResult с группами (отсортированы по убыванию суммы),
        кандидатами в «скрытые подписки» и итоговой суммой.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"strategy must be one of {STRATEGIES}")

    operations, meta = parse_statement_detailed(source)
    df = operations_to_frame(operations)
    if df.empty:
        raise ValueError("Не удалось извлечь операции из выписки")

    all_expenses = df[~df["is_income"]].copy()

    # --- Полные месяцы: частичные крайние месяцы исключаются целиком ------
    full, excluded_periods = determine_full_months(all_expenses, meta.formation_date)
    if not full:
        # страховка от вырожденного периода: считаем по всем месяцам
        full, excluded_periods = _month_range(all_expenses), []

    expenses = all_expenses[all_expenses["month"].isin(full)].copy()
    months = full  # далее везде используем только полные месяцы

    # --- Скрытые регулярные переводы --------------------------------------
    raw_candidates = find_regular_transfers(
        expenses, months, min_month_share, amount_tolerance
    )
    candidates = apply_decisions(raw_candidates, load_decisions(decisions))

    # Изолируем регулярные переводы из общей транзитной группы «Переводы»
    is_candidate = expenses["group"].eq(TRANSFERS_GROUP) & expenses[
        "counterparty"
    ].isin([c.counterparty for c in candidates])
    regular_expenses = expenses[~is_candidate].copy()

    resolved = [
        GroupResult(
            name=c.label or f"Перевод: {c.counterparty}",
            monthly_amount=c.amount,
            ops_count=1,
            description="подтверждённый регулярный перевод (услуга)",
            included=bool(c.include),
            operations=[f"{_shorten(c.counterparty)} — {fmt_money(c.amount)} руб."],
        )
        for c in candidates
        if c.include
    ]

    # --- Агрегация групп расходов за полные месяцы -------------------------
    groups = _aggregate_groups(regular_expenses, months, strategy, min_month_share)
    included = [
        g for g in groups
        if g.included and g.name not in {TRANSFERS_GROUP, CASH_GROUP}
    ]
    excluded = [g for g in groups if g not in included]

    included += [r for r in resolved if r.included]
    included.sort(key=lambda g: -g.monthly_amount)
    excluded.sort(key=lambda g: -g.monthly_amount)

    total = round(sum(g.monthly_amount for g in included), 2)
    return CushionResult(
        period_start=str(months[0]) if months else "",
        period_end=str(months[-1]) if months else "",
        months_analyzed=len(months),
        cushion_total=total,
        full_months=[_month_label(m) for m in months],
        excluded_months=[_month_label(m) for m in excluded_periods],
        groups=included,
        candidates=candidates,
        excluded_groups=excluded,
    )


# ==========================================================================
# Двухэтапный сценарий: analyze -> (пользователь правит JSON) -> recalculate
# ==========================================================================


@dataclass
class TxRecord:
    """Транзакция, которую пользователь может править и возвращать назад.

    Правила учёта в пересчёте (recalculate):
      - обычная трата учитывается при ``is_active=True``;
      - p2p-перевод учитывается при ``include_in_cushion=True`` и
        попадает в отчёт под названием ``transfer_label`` (заданная
        пользователем категория услуги) либо «Перевод: <контрагент>».
    """

    tx_id: str                      # уникальный ID (uuid4 hex)
    date: str                       # ISO-дата, 'YYYY-MM-DD'
    group: str                      # категория, определённая алгоритмом
    counterparty: str               # мерчант / ФИО контрагента
    amount: float                   # сумма списания, руб.
    is_regular: bool = False        # входит ли в регулярные траты алгоритма
    is_active: bool = True          # флаг пользователя: учитывать ли трату
    is_transfer: bool = False       # регулярный p2p-перевод (кандидат)
    transfer_label: Optional[str] = None    # пользовательская категория
    include_in_cushion: bool = False        # включить ли перевод в подушку


@dataclass
class StatementAnalysis:
    """Результат первого шага — редактируемый пользовательский JSON."""

    full_months: List[str]                      # полные месяцы («июнь 2026»)
    excluded_months: List[str]                  # отброшенные частичные месяцы
    months_analyzed: int
    transactions: List[TxRecord]
    transfer_candidates: List[TransferCandidate] = field(default_factory=list)


def _make_tx_records(
    expenses: pd.DataFrame,
    months: Sequence[pd.Period],
    min_month_share: float,
    candidates: Sequence[TransferCandidate],
) -> List[TxRecord]:
    """Расходы за полные месяцы -> список редактируемых TxRecord.

    ``is_active=True`` по умолчанию выставляется только регулярным
    тратам (группа встречалась в >= min_month_share доле полных
    месяцев и не является транзитной); нерегулярные операции
    возвращаются с ``is_active=False`` — пользователь может включить
    их вручную. Регулярные p2p-переводы помечаются ``is_transfer``
    и по умолчанию НЕ учитываются (решение — за пользователем).
    """
    n_months = len(months)
    min_months = max(1, math.ceil(min_month_share * n_months))
    cand_map = {
        " ".join(c.counterparty.lower().split()): c for c in candidates
    }
    months_per_group = expenses.groupby("group")["month"].nunique().to_dict()

    records: List[TxRecord] = []
    for row in expenses.itertuples():
        key = " ".join(row.counterparty.lower().split())
        cand = cand_map.get(key)
        is_transfer = row.group == TRANSFERS_GROUP and cand is not None
        is_regular = (
            months_per_group.get(row.group, 0) >= min_months
            and row.group not in TRANSIT_CATEGORIES
        )
        records.append(
            TxRecord(
                tx_id=uuid.uuid4().hex,
                date=row.date.date().isoformat(),
                group=str(row.group),
                counterparty=str(row.counterparty),
                amount=float(row.amount),
                is_regular=is_regular or is_transfer,
                is_active=bool(is_regular) and not is_transfer,
                is_transfer=is_transfer,
                transfer_label=cand.label if cand else None,
                include_in_cushion=bool(cand.include) if cand else False,
            )
        )
    records.sort(key=lambda r: (r.date, -r.amount))
    return records


def analyze_statement(
    source: Union[str, bytes, Path],
    decisions: Union[str, Path, dict, None] = None,
    min_month_share: float = 0.5,
    amount_tolerance: float = 0.10,
) -> StatementAnalysis:
    """Шаг 1: PDF-выписка -> редактируемый структурированный JSON.

    Находит полные месяцы, группирует регулярные траты и p2p-переводы,
    присваивает каждой транзакции уникальный ID. В итоговом JSON все
    регулярные траты имеют ``is_active=True``, нерегулярные — False.
    """
    operations, meta = parse_statement_detailed(source)
    df = operations_to_frame(operations)
    if df.empty:
        raise ValueError("Не удалось извлечь операции из выписки")

    all_expenses = df[~df["is_income"]].copy()
    full, excluded_periods = determine_full_months(all_expenses, meta.formation_date)
    if not full:
        full, excluded_periods = _month_range(all_expenses), []

    expenses = all_expenses[all_expenses["month"].isin(full)].copy()
    candidates = apply_decisions(
        find_regular_transfers(expenses, full, min_month_share, amount_tolerance),
        load_decisions(decisions),
    )
    return StatementAnalysis(
        full_months=[_month_label(m) for m in full],
        excluded_months=[_month_label(m) for m in excluded_periods],
        months_analyzed=len(full),
        transactions=_make_tx_records(expenses, full, min_month_share, candidates),
        transfer_candidates=candidates,
    )


def filter_transactions(
    transactions: Sequence[TxRecord],
    exclude_tx_ids: Sequence[str] = (),
    exclude_merchants: Sequence[str] = (),
) -> List[TxRecord]:
    """Фильтрация транзакций по списку исключений.

    Args:
        transactions: исходный список TxRecord.
        exclude_tx_ids: ID транзакций (uuid), которые исключить.
        exclude_merchants: названия торговых точек/контрагентов;
            исключается любая транзакция, в имени которой встречается
            подстрока (регистр не важен).
    """
    ids = {str(i).strip().lower() for i in exclude_tx_ids if str(i).strip()}
    merchants = [str(m).strip().lower() for m in exclude_merchants if str(m).strip()]
    result: List[TxRecord] = []
    for tx in transactions:
        if tx.tx_id.lower() in ids:
            continue
        if merchants and any(m in tx.counterparty.lower() for m in merchants):
            continue
        result.append(tx)
    return result


def filter_frame(
    df: pd.DataFrame,
    exclude_tx_ids: Sequence[str] = (),
    exclude_merchants: Sequence[str] = (),
) -> pd.DataFrame:
    """То же исключение, но для DataFrame с колонками tx_id/counterparty."""
    out = df
    if exclude_tx_ids:
        ids = {str(i).strip().lower() for i in exclude_tx_ids if str(i).strip()}
        out = out[~out["tx_id"].str.lower().isin(ids)]
    if exclude_merchants:
        merchants = [str(m).strip().lower() for m in exclude_merchants if str(m).strip()]
        lowered = out["counterparty"].str.lower()
        for m in merchants:
            out = out[~lowered.str.contains(m, regex=False)]
    return out


def _aggregate_active(
    df: pd.DataFrame,
    months: int,
    counted_description: str,
) -> List[GroupResult]:
    """Агрегация активных трат по группам: сумма / число полных месяцев."""
    results: List[GroupResult] = []
    for group, grp in df.groupby("group"):
        group = str(group)
        sorted_grp = grp.sort_values("amount", ascending=False)
        results.append(
            GroupResult(
                name=group,
                monthly_amount=round(float(grp["amount"].sum()) / months, 2),
                ops_count=math.ceil(len(grp) / months),
                description=counted_description
                if group.startswith("Перевод:")
                else description_for_group(group),
                included=True,
                operations=[
                    f"{_shorten(cp)} — {fmt_money(a)} руб."
                    for cp, a in zip(sorted_grp["counterparty"], sorted_grp["amount"])
                ],
            )
        )
    return results


def recalculate(
    transactions: Sequence[TxRecord],
    months_analyzed: int,
    full_months: Sequence[str] = (),
    excluded_months: Sequence[str] = (),
    exclude_tx_ids: Sequence[str] = (),
    exclude_merchants: Sequence[str] = (),
) -> CushionResult:
    """Шаг 2: пересчёт подушки по изменённому пользователем набору.

    Формула: [Сумма всех активных трат] / [Количество полных месяцев].

    Учитываются:
      - обычные траты с ``is_active=True``;
      - p2p-переводы с ``include_in_cushion=True`` (под пользовательской
        категорией ``transfer_label``);
      - минус переданные списки исключений (ID или названия точек).

    Args:
        transactions: правеный пользователем список TxRecord.
        months_analyzed: число полных месяцев (знаменатель).
        full_months/excluded_months: подписи месяцев для отчёта.
        exclude_tx_ids: доп. исключение по ID транзакций.
        exclude_merchants: доп. исключение по названиям торговых точек.

    Returns:
        CushionResult с группами, отсортированными по убыванию суммы.
    """
    months = max(1, int(months_analyzed))
    kept = filter_transactions(transactions, exclude_tx_ids, exclude_merchants)

    rows = []
    for tx in kept:
        if tx.is_transfer:
            counted = bool(tx.include_in_cushion)
            group = tx.transfer_label or f"Перевод: {tx.counterparty}"
        else:
            counted = bool(tx.is_active)
            group = tx.group
        rows.append(
            {
                "group": group,
                "amount": tx.amount,
                "counterparty": tx.counterparty,
                "counted": counted,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty or not df["counted"].any():
        active, inactive = df.iloc[0:0], df
    else:
        active = df[df["counted"]]
        inactive = df[~df["counted"]]

    groups = _aggregate_active(active, months, "активная регулярная трата")
    groups.sort(key=lambda g: -g.monthly_amount)

    excluded_groups = _aggregate_active(inactive, months, "исключено пользователем")
    excluded_groups.sort(key=lambda g: -g.monthly_amount)

    total = (
        round(float(active["amount"].sum()) / months, 2)
        if not active.empty
        else 0.0
    )
    return CushionResult(
        period_start="",
        period_end="",
        months_analyzed=months,
        cushion_total=total,
        full_months=list(full_months),
        excluded_months=list(excluded_months),
        groups=groups,
        candidates=[],
        excluded_groups=excluded_groups,
    )
