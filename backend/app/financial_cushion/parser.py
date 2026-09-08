"""Извлечение операций из PDF-выписки платёжного счёта Сбербанка.

Структура документа (SberBank Online, «Выписка по платёжному счёту»):
  - строка-заголовок операции:
        DD.MM.YYYY HH:MM КАТЕГОРИЯ [+|]СУММА ОСТАТОК
    (поступления помечены знаком «+», списания — без знака);
  - строка(и)-описание операции:
        DD.MM.YYYY КОД_АВТОРИЗАЦИИ ОПИСАНИЕ. Операция по карте/счету ****XXXX
    описание может переноситься на следующую строку.

Возвращает список операций: дата, категория, сумма (положительная),
признак дохода/расхода, описание, контрагент/мерчант, а также
метаданные документа (дата формирования, период выписки).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Union

import pdfplumber

# Строка-заголовок операции: дата, время, категория, [+]сумма, остаток
HEADER_RE = re.compile(
    r"^(?P<date>\d{2}\.\d{2}\.\d{4})\s+(?P<time>\d{2}:\d{2})\s+"
    r"(?P<category>.+?)\s+"
    r"(?P<sign>\+)?(?P<amount>\d[\d\s\u00a0]*,\d{2})\s+"
    r"(?P<balance>\d[\d\s\u00a0]*,\d{2})\s*$"
)

# Строка-описание операции: дата обработки, код авторизации, текст
DETAIL_RE = re.compile(
    r"^(?P<date>\d{2}\.\d{2}\.\d{4})\s+(?P<code>\d{6})\s+(?P<text>.+)$"
)

# Служебные строки, которые не являются операциями
SKIP_RE = re.compile(
    r"Продолжение на следующей|Выписка по платёжному счёту|"
    r"ДАТА ОПЕРАЦИИ|Дата обработки|и код авторизации|Расшифровка операций|"
    r"Для проверки|ПАО Сбербанк|Дата формирования|ИТОГО ПО ОПЕРАЦИЯМ|"
    r"^\s*\*\s*$|^\s*\d{1,2}\s*$|www\.sberbank\.ru|в верхнем правом углу|"
    r"Получите документ|Нажмите кнопку|Зайдите в приложение|"
    r"Предоставляя QR-код|Действителен|до \d{2}\.\d{2}\.\d{4}|"
    r"^\s*$"
)

# Метаданные документа (нужны для определения «полных» месяцев)
FORMATION_RE = re.compile(r"Дата формирования документа\s+(\d{2}\.\d{2}\.\d{4})")
PERIOD_RE = re.compile(
    r"За период\s+(\d{2}\.\d{2}\.\d{4})\s*[—–-]\s*(\d{2}\.\d{2}\.\d{4})"
)


@dataclass
class StatementMeta:
    """Метаданные выписки."""

    formation_date: Optional[datetime] = None  # дата формирования документа
    period_start: Optional[datetime] = None    # начало периода выписки
    period_end: Optional[datetime] = None      # конец периода выписки


@dataclass
class Operation:
    """Одна операция выписки."""

    date: datetime
    category: str          # категория Сбера (Супермаркеты, Перевод СБП, ...)
    amount: float          # сумма по модулю, в рублях
    is_income: bool        # True — поступление (+), False — списание
    description: str       # описание операции (мерчант/контрагент/назначение)
    balance: float         # остаток средств после операции

    @property
    def counterparty(self) -> str:
        """Контрагент: ФИО получателя перевода или название мерчанта."""
        return extract_counterparty(self.description)


def to_float(raw: str) -> float:
    """'8 774,70' -> 8774.70."""
    return float(
        raw.replace("\u00a0", "").replace(" ", "").replace(",", ".")
    )


def parse_date(raw: str) -> datetime:
    return datetime.strptime(raw, "%d.%m.%Y")


def extract_counterparty(description: str) -> str:
    """Извлекает контрагента из описания операции.

    - «Перевод для И. Иван Иванович. Операция по счету» -> «И. Иван Иванович»
    - «Перевод в Ozon Bank (Ozon). Операция по счету»   -> «Ozon Bank (Ozon)»
    - «PYATEROCHKA 4732 Ekaterinburg RUS. Операция по карте» -> мерчант
    """
    desc = " ".join(description.split())
    m = re.match(r"Перевод (?:для|в|от)\s+(?P<name>.+?)\. Операция", desc)
    if m:
        return m.group("name").strip()
    m = re.match(r"(?P<merchant>.+?)\. Операция", desc)
    if m:
        return m.group("merchant").strip()
    return desc.strip(" .")


def _iter_lines(source: Union[str, bytes, Path]) -> Iterable[str]:
    """Итератор по строкам текста всех страниц PDF."""
    if isinstance(source, (str, Path)):
        opener = pdfplumber.open(str(source))
    else:  # bytes / BytesIO — например, файл из HTTP-запроса
        import io

        opener = pdfplumber.open(io.BytesIO(source))
    with opener as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                yield line


def parse_statement_detailed(
    source: Union[str, bytes, Path],
) -> Tuple[List[Operation], StatementMeta]:
    """Разбирает PDF-выписку Сбербанка в список операций + метаданные.

    Args:
        source: путь к PDF-файлу либо его содержимое в виде bytes.

    Returns:
        (список Operation — и поступления, и списания; StatementMeta
        с датой формирования и периодом выписки).
    """
    operations: List[Operation] = []
    pending: Optional[Operation] = None
    meta = StatementMeta()

    for line in _iter_lines(source):
        # Метаданные встречаются среди служебных строк — извлекаем
        # до проверки SKIP_RE.
        m = FORMATION_RE.search(line)
        if m:
            meta.formation_date = parse_date(m.group(1))
        m = PERIOD_RE.search(line)
        if m:
            meta.period_start = parse_date(m.group(1))
            meta.period_end = parse_date(m.group(2))

        if SKIP_RE.search(line):
            continue

        header = HEADER_RE.match(line)
        if header:
            pending = Operation(
                date=parse_date(header.group("date")),
                category=header.group("category").strip(),
                amount=to_float(header.group("amount")),
                is_income=header.group("sign") == "+",
                description="",
                balance=to_float(header.group("balance")),
            )
            operations.append(pending)
            continue

        detail = DETAIL_RE.match(line)
        if detail and pending is not None:
            pending.description = detail.group("text").strip()
            continue

        if pending is not None:
            # перенос описания на следующую строку
            pending.description += " " + line.strip()

    for op in operations:
        op.description = " ".join(op.description.split())
    return operations, meta


def parse_statement(source: Union[str, bytes, Path]) -> List[Operation]:
    """Разбирает PDF-выписку Сбербанка в список операций (без метаданных)."""
    return parse_statement_detailed(source)[0]
