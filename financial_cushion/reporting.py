"""Формирование текстового отчёта «финансовая подушка».

Формат (категории строго по убыванию суммы):

    Ваша финансовая подушка на следующий месяц: х рублей
    -- [Категория] - х рублей (Количество операций: х) — описание
       • операция — сумма
    ...

    Внимание! Обнаружены регулярные переводы, которые могут быть
    скрытыми подписками или услугами:
    - Перевод контрагенту [Имя/Номер] на сумму ~х рублей,
      повторялся х раз(а). Как классифицировать этот расход и
      включать ли его в подушку?
"""
from __future__ import annotations

from typing import Iterable, List

from .analyzer import CushionResult, GroupResult, TransferCandidate, fmt_money


def _fmt_money(value: float) -> str:
    return fmt_money(value)


def _format_group(group: GroupResult, with_operations: bool = True) -> List[str]:
    """Строка категории + краткий список её операций."""
    lines = [
        f"-- {group.name} - {_fmt_money(group.monthly_amount)} рублей "
        f"(Количество операций: {group.ops_count}) — {group.description}"
    ]
    if with_operations:
        lines += [f"   • {op}" for op in group.operations]
    return lines


def _format_pending_candidates(
    candidates: Iterable[TransferCandidate],
) -> List[str]:
    lines: List[str] = []
    pending = [c for c in candidates if c.include is None]
    if not pending:
        return lines
    lines.append("")
    lines.append(
        "Внимание! Обнаружены регулярные переводы, которые могут быть "
        "скрытыми подписками или услугами:"
    )
    for cand in pending:
        lines.append(
            f"- Перевод контрагенту [{cand.counterparty}] на сумму "
            f"~{_fmt_money(cand.amount)} рублей, повторялся "
            f"{cand.occurrences} раз(а). Как классифицировать этот расход "
            f"и включать ли его в подушку?"
        )
    return lines


def _format_resolved_note(result: CushionResult) -> List[str]:
    if not result.candidates:
        return []
    lines: List[str] = [""]
    confirmed = [c for c in result.candidates if c.include]
    declined = [c for c in result.candidates if c.include is False]
    if confirmed:
        lines.append("Регулярные переводы, включённые в подушку по вашему решению:")
        for cand in confirmed:
            name = cand.label or cand.counterparty
            lines.append(f"- {name} — {_fmt_money(cand.amount)} рублей/мес")
    if declined:
        lines.append("Регулярные переводы, исключённые из подушки по вашему решению:")
        for cand in declined:
            lines.append(f"- {cand.counterparty} — {_fmt_money(cand.amount)} рублей/мес")
    return lines


def build_report(
    result: CushionResult,
    pending_only: bool = False,
) -> str:
    """Строит текстовый отчёт по результату расчёта.

    Args:
        result: результат calculate_cushion / recalculate.
        pending_only: True — показать только итог и блок уточнений
            (используется на первом шаге интерактивного сценария).
    """
    lines: List[str] = [
        f"Ваша финансовая подушка на следующий месяц: "
        f"{_fmt_money(result.cushion_total)} рублей"
    ]

    if not pending_only:
        period_line = (
            f"(расчёт по {result.months_analyzed} полн. мес.: "
            f"{', '.join(result.full_months)})"
        )
        if result.excluded_months:
            period_line += (
                f"; исключён частичный месяц: {', '.join(result.excluded_months)}"
            )
        lines.append(period_line)
        for group in result.groups:
            lines += _format_group(group)
        lines += _format_resolved_note(result)

    lines += _format_pending_candidates(result.candidates)

    if not pending_only and result.excluded_groups:
        lines.append("")
        lines.append("Не включено в подушку (нерегулярные / транзитные):")
        for group in result.excluded_groups:
            lines += _format_group(group)

    return "\n".join(lines)
