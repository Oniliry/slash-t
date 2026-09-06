"""Async API сервиса финансовой подушки (FastAPI).

Запуск:
    uvicorn financial_cushion.api:app --host 0.0.0.0 --port 8080

Двухэтапный сценарий (интерактивное редактирование пользователем):
    POST /analyze-statement   — PDF -> редактируемый JSON (uuid транзакций,
                                is_active=true у регулярных трат)
    POST /recalculate-cushion — изменённый JSON -> пересчитанная подушка
                                ([сумма активных трат] / [число полных
                                месяцев])

Одноэтапный сценарий для совместимости:
    POST /analyze             — PDF сразу в готовый отчёт.

CPU-bound расчёт (pandas) выполняется в рабочем потоке через
``asyncio.to_thread`` и не блокирует event loop.
"""
from __future__ import annotations

import asyncio
import json
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, model_validator

from .analyzer import (
    STRATEGIES,
    CushionResult,
    StatementAnalysis,
    TxRecord,
    analyze_statement,
    calculate_cushion,
    recalculate,
)
from .reporting import build_report

app = FastAPI(
    title="Financial Cushion Service",
    description="Расчёт минимальных расходов на месяц по PDF-выписке Сбербанка",
    version="2.0.0",
)


# ---------------------------------------------------------------------------
# Модели: шаг 1 — /analyze-statement
# ---------------------------------------------------------------------------


class TxDTO(BaseModel):
    """Транзакция, редактируемая пользователем (round-trip JSON)."""

    tx_id: str = Field(..., description="уникальный ID транзакции (uuid4 hex)")
    date: str = Field(..., description="дата операции, YYYY-MM-DD")
    group: str = Field(..., description="категория, определённая алгоритмом")
    counterparty: str = Field(..., description="мерчант / ФИО контрагента")
    amount: float = Field(..., gt=0, description="сумма списания, руб.")
    is_regular: bool = Field(False, description="регулярная ли трата по мнению алгоритма")
    is_active: bool = Field(
        True,
        description="учитывать ли трату в пересчёте (пользователь может выключить)",
    )
    is_transfer: bool = Field(
        False, description="true — регулярный p2p-перевод (кандидат в услуги)"
    )
    transfer_label: Optional[str] = Field(
        None, description="пользовательская категория услуги для перевода"
    )
    include_in_cushion: bool = Field(
        False,
        description="для переводов: включать ли в подушку (аналог «include»)",
    )


class TransferCandidateDTO(BaseModel):
    """Подсказка UI: регулярный перевод, требующий решения."""

    counterparty: str
    amount: float
    occurrences: int


class StatementAnalysisResponse(BaseModel):
    """Ответ /analyze-statement — пользователь правит его и отправляет назад."""

    full_months: List[str] = Field(..., description="полные месяцы периода")
    excluded_months: List[str] = Field(..., description="отброшенные частичные месяцы")
    months_analyzed: int = Field(..., ge=1, description="число полных месяцев")
    transactions: List[TxDTO]
    transfer_candidates: List[TransferCandidateDTO] = []


# ---------------------------------------------------------------------------
# Модели: шаг 2 — /recalculate-cushion
# ---------------------------------------------------------------------------


class RecalcRequest(BaseModel):
    """Изменённый пользователем JSON + опциональные списки исключений."""

    months_analyzed: Optional[int] = Field(
        None, ge=1,
        description="число полных месяцев (можно не слать, если есть full_months)",
    )
    full_months: List[str] = Field(
        default_factory=list, description="подписи полных месяцев для отчёта"
    )
    excluded_months: List[str] = Field(
        default_factory=list, description="отброшенные частичные месяцы"
    )
    transactions: List[TxDTO]
    exclude_tx_ids: List[str] = Field(
        default_factory=list, description="доп. исключение транзакций по ID"
    )
    exclude_merchants: List[str] = Field(
        default_factory=list,
        description="доп. исключение по названию торговой точки (подстрока)",
    )

    @model_validator(mode="after")
    def _check_denominator(self) -> "RecalcRequest":
        if self.months_analyzed is None and not self.full_months:
            raise ValueError(
                "Нужен months_analyzed либо непустой full_months "
                "(знаменатель формулы пересчёта)"
            )
        return self


class GroupDTO(BaseModel):
    name: str
    monthly_amount: float
    ops_count: int
    description: str
    included: bool
    operations: list[str] = []


class RecalcResponse(BaseModel):
    months_analyzed: int
    cushion_total: float
    report: str
    groups: List[GroupDTO]
    excluded_groups: List[GroupDTO]


# ---------------------------------------------------------------------------
# Конвертеры dataclass <-> DTO
# ---------------------------------------------------------------------------


def _analysis_to_response(analysis: StatementAnalysis) -> StatementAnalysisResponse:
    return StatementAnalysisResponse(
        full_months=analysis.full_months,
        excluded_months=analysis.excluded_months,
        months_analyzed=analysis.months_analyzed,
        transactions=[TxDTO(**tx.__dict__) for tx in analysis.transactions],
        transfer_candidates=[
            TransferCandidateDTO(
                counterparty=c.counterparty,
                amount=c.amount,
                occurrences=c.occurrences,
            )
            for c in analysis.transfer_candidates
        ],
    )


def _request_to_records(request: RecalcRequest) -> List[TxRecord]:
    return [
        TxRecord(
            tx_id=t.tx_id,
            date=t.date,
            group=t.group,
            counterparty=t.counterparty,
            amount=t.amount,
            is_regular=t.is_regular,
            is_active=t.is_active,
            is_transfer=t.is_transfer,
            transfer_label=t.transfer_label,
            include_in_cushion=t.include_in_cushion,
        )
        for t in request.transactions
    ]


def _result_to_response(result: CushionResult) -> RecalcResponse:
    return RecalcResponse(
        months_analyzed=result.months_analyzed,
        cushion_total=result.cushion_total,
        report=build_report(result),
        groups=[GroupDTO(**g.__dict__) for g in result.groups],
        excluded_groups=[GroupDTO(**g.__dict__) for g in result.excluded_groups],
    )


# ---------------------------------------------------------------------------
# Эндпоинты
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/analyze-statement", response_model=StatementAnalysisResponse)
async def analyze_statement_endpoint(
    file: UploadFile = File(..., description="PDF-выписка Сбербанка"),
    decisions: Optional[str] = Form(
        default=None,
        description=(
            'Необязательный JSON с предрешениями по переводам: '
            '{"Г. Санан": {"label": "Аренда", "include": true}}'
        ),
    ),
    min_month_share: float = Query(0.5, gt=0.0, le=1.0),
    amount_tolerance: float = Query(0.10, gt=0.0, le=1.0),
) -> StatementAnalysisResponse:
    """Шаг 1: разобрать PDF и вернуть редактируемый JSON транзакций."""
    if (file.content_type or "") not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(415, "Ожидается PDF-файл")
    payload = await file.read()
    try:
        parsed_decisions = json.loads(decisions) if decisions else None
    except json.JSONDecodeError as exc:
        raise HTTPException(400, f"decisions: некорректный JSON: {exc}") from exc
    try:
        analysis = await asyncio.to_thread(
            analyze_statement,
            payload,
            parsed_decisions,
            min_month_share,
            amount_tolerance,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return _analysis_to_response(analysis)


@app.post("/recalculate-cushion", response_model=RecalcResponse)
async def recalculate_cushion_endpoint(request: RecalcRequest) -> RecalcResponse:
    """Шаг 2: пересчитать подушку по изменённому пользователем JSON.

    Формула: [сумма всех активных трат] / [количество полных месяцев].
    """
    months = request.months_analyzed or len(request.full_months)
    records = _request_to_records(request)
    try:
        result = await asyncio.to_thread(
            recalculate,
            records,
            months,
            request.full_months,
            request.excluded_months,
            request.exclude_tx_ids,
            request.exclude_merchants,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return _result_to_response(result)


@app.post("/analyze", response_model=RecalcResponse)
async def analyze_legacy(
    file: UploadFile = File(..., description="PDF-выписка Сбербанка"),
    decisions: Optional[str] = Form(
        default=None,
        description=(
            'JSON-строка вида {"И. Иван Иванович": '
            '{"label": "Репетитор", "include": true}}'
        ),
    ),
    strategy: str = Query("mean", description=f"one of {STRATEGIES}"),
    min_month_share: float = Query(0.5, gt=0.0, le=1.0),
    amount_tolerance: float = Query(0.10, gt=0.0, le=1.0),
) -> RecalcResponse:
    """Одноэтапный расчёт (совместимость): PDF сразу в готовый отчёт."""
    if (file.content_type or "") not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(415, "Ожидается PDF-файл")

    payload = await file.read()
    try:
        parsed_decisions = json.loads(decisions) if decisions else None
    except json.JSONDecodeError as exc:
        raise HTTPException(400, f"decisions: некорректный JSON: {exc}") from exc

    try:
        result = await asyncio.to_thread(
            calculate_cushion,
            payload,
            parsed_decisions,
            strategy,
            min_month_share,
            amount_tolerance,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return _result_to_response(result)
