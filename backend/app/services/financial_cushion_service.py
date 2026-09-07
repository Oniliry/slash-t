import asyncio
from dataclasses import asdict
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from database.models.user import User
from database.repositories.financial_cushion_repo import CushionAnalysisRepository
from financial_cushion.analyzer import (
    TxRecord,
    analyze_statement,
    recalculate,
)
from schemas.base import APIResponse
from schemas.financial_cushion import (
    FamilyCushionRatingItem,
    StatementAnalysisResponse,
    StatementGroupDTO,
    StatementRecalculateRequest,
    StatementRecalculateResponse,
    StatementTxDTO,
    TransferCandidateDTO,
)

#: Максимальный размер PDF-выписки — 10 МБ.
MAX_PDF_SIZE = 10 * 1024 * 1024

#: Допустимые content-type для загрузки выписки.
ALLOWED_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}


class FinancialCushionService:
    """Сервис анализа PDF-выписок: расчёт финподушки участника семьи.

    Использует готовый алгоритм пакета financial_cushion:
    analyze_statement() (шаг 1 — разбор PDF в редактируемый JSON) и
    recalculate() (шаг 2 — пересчёт по правкам пользователя). CPU-bound
    расчёты pandas выполняются в рабочем потоке через asyncio.to_thread.
    """

    def __init__(self, analysis_repo: CushionAnalysisRepository):
        """
        Инициализация сервиса.

        :param analysis_repo: Репозиторий сохранённых анализов выписок.
        """
        self.analysis_repo = analysis_repo

    async def upload_statement(self, user: User, file) -> APIResponse:
        """
        Принимает PDF-выписку, прогоняет через готовый алгоритм и
        сохраняет результат за текущим пользователем.

        :param user: Текущий авторизованный пользователь.
        :param file: Загруженный файл выписки (multipart).
        :return: Разобранный JSON анализа или ошибку валидации/разбора.
        """
        family_error = self._family_error(user)
        if family_error is not None:
            return family_error

        validation_error = await self._validate_pdf(file)
        if validation_error is not None:
            return validation_error

        payload = await file.read()

        try:
            analysis = await asyncio.to_thread(analyze_statement, payload)
        except ValueError as exc:
            return APIResponse.fail(
                message=str(exc),
                status_code=422,
                type="analysis_failed",
            )
        except Exception:
            return APIResponse.fail(
                message="Не удалось разобрать PDF-выписку. "
                        "Убедитесь, что это выписка Сбербанка.",
                status_code=422,
                type="analysis_failed",
            )

        payload_dict = asdict(analysis)
        months = analysis.months_analyzed
        cushion_total = self._total_of(analysis.transactions, months)

        await self.analysis_repo.upsert_analysis(
            user_id=user.id,
            family_id=user.family_id,
            months_analyzed=months,
            cushion_total=cushion_total,
            full_months=analysis.full_months,
            excluded_months=analysis.excluded_months,
            payload=payload_dict,
        )

        return APIResponse.success(
            StatementAnalysisResponse(
                full_months=analysis.full_months,
                excluded_months=analysis.excluded_months,
                months_analyzed=months,
                transactions=[StatementTxDTO(**asdict(tx)) for tx in analysis.transactions],
                transfer_candidates=[
                    TransferCandidateDTO(
                        counterparty=c.counterparty,
                        amount=c.amount,
                        occurrences=c.occurrences,
                    )
                    for c in analysis.transfer_candidates
                ],
            )
        )

    async def recalculate(self, user: User, request: StatementRecalculateRequest) -> APIResponse:
        """
        Пересчитывает подушку по правкам пользователя (флаги is_active,
        include_in_cushion, transfer_label) и обновляет его итог.

        :param user: Текущий авторизованный пользователь.
        :param request: Изменённый пользователем JSON транзакций.
        :return: Пересчитанный отчёт или ошибку валидации.
        """
        family_error = self._family_error(user)
        if family_error is not None:
            return family_error

        months = request.months_analyzed or len(request.full_months)
        records = [
            TxRecord(
                tx_id=tx.tx_id,
                date=tx.date,
                group=tx.group,
                counterparty=tx.counterparty,
                amount=tx.amount,
                is_regular=tx.is_regular,
                is_active=tx.is_active,
                is_transfer=tx.is_transfer,
                transfer_label=tx.transfer_label,
                include_in_cushion=tx.include_in_cushion,
            )
            for tx in request.transactions
        ]

        try:
            result = await asyncio.to_thread(
                recalculate,
                records,
                months,
                request.full_months,
                request.excluded_months,
            )
        except ValueError as exc:
            return APIResponse.fail(
                message=str(exc),
                status_code=422,
                type="recalculate_failed",
            )

        cushion_total = Decimal(str(result.cushion_total)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        transactions_payload = [tx.model_dump() for tx in request.transactions]

        saved = await self.analysis_repo.get_user_analysis(user.id)
        if saved is not None:
            payload = dict(saved.payload)
            payload["transactions"] = transactions_payload
            await self.analysis_repo.update_cushion_total(
                user.id, cushion_total, payload
            )

        return APIResponse.success(
            StatementRecalculateResponse(
                months_analyzed=result.months_analyzed,
                cushion_total=float(result.cushion_total),
                groups=[self._group_dto(g) for g in result.groups],
                excluded_groups=[self._group_dto(g) for g in result.excluded_groups],
            )
        )

    async def get_last(self, user: User) -> APIResponse:
        """
        Возвращает последний анализ выписки текущего пользователя.

        :param user: Текущий авторизованный пользователь.
        :return: Сохранённый JSON анализа или data: null, если его нет.
        """
        family_error = self._family_error(user)
        if family_error is not None:
            return family_error

        saved = await self.analysis_repo.get_user_analysis(user.id)
        if saved is None:
            return APIResponse.success(None)

        return APIResponse.success(self._saved_to_response(saved))

    async def family_summary(self, user: User) -> APIResponse:
        """
        Возвращает рейтинг участников семьи по убыванию финподушки.

        :param user: Текущий авторизованный пользователь.
        :return: Список участников с их суммами подушки.
        """
        family_error = self._family_error(user)
        if family_error is not None:
            return family_error

        rows = await self.analysis_repo.get_family_summary(user.family_id)
        return APIResponse.success(
            [
                FamilyCushionRatingItem(
                    user_id=row["user_id"],
                    user_name=row["user_name"],
                    cushion_total=float(row["cushion_total"]),
                    months_analyzed=row["months_analyzed"],
                )
                for row in rows
            ]
        )

    async def reset(self, user: User) -> APIResponse:
        """
        Удаляет сохранённый анализ текущего пользователя.

        :param user: Текущий авторизованный пользователь.
        :return: Пустой успешный ответ.
        """
        family_error = self._family_error(user)
        if family_error is not None:
            return family_error

        await self.analysis_repo.delete_analysis(user.id)
        return APIResponse.success(None, message="Анализ сброшен.")

    # ------------------------------------------------------------------

    @staticmethod
    def _family_error(user: User):
        """Проверка наличия семьи у пользователя (общая ошибка 403)."""
        if user.family_id is None:
            return APIResponse.fail(
                message="Сначала создайте семью или присоединитесь к ней.",
                status_code=403,
                type="family_required",
            )
        return None

    @staticmethod
    async def _validate_pdf(file) -> APIResponse:
        """Проверка content-type и размера загружаемого PDF."""
        content_type = (file.content_type or "").split(";")[0].strip().lower()
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            return APIResponse.fail(
                message="Ожидается PDF-файл выписки.",
                status_code=415,
                type="unsupported_media_type",
            )
        size = getattr(file, "size", None)
        if size is not None and size > MAX_PDF_SIZE:
            return APIResponse.fail(
                message="Файл слишком большой: максимум 10 МБ.",
                status_code=413,
                type="file_too_large",
            )
        return None

    @staticmethod
    def _total_of(transactions: List[TxRecord], months: int) -> Decimal:
        """Итог анализа: [сумма активных трат] / [число полных месяцев]."""
        if months < 1:
            months = 1
        active_sum = sum(tx.amount for tx in transactions if tx.is_active)
        return (Decimal(str(active_sum)) / Decimal(months)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @staticmethod
    def _group_dto(group) -> StatementGroupDTO:
        """GroupResult готового пакета -> StatementGroupDTO."""
        return StatementGroupDTO(
            name=group.name,
            monthly_amount=group.monthly_amount,
            ops_count=group.ops_count,
            total_amount=group.total_amount,
            description=group.description,
            operations=list(group.operations),
        )

    @staticmethod
    def _saved_to_response(saved) -> StatementAnalysisResponse:
        """Сохранённый payload из БД -> StatementAnalysisResponse."""
        payload = saved.payload or {}
        return StatementAnalysisResponse(
            full_months=saved.full_months or payload.get("full_months", []),
            excluded_months=saved.excluded_months or payload.get("excluded_months", []),
            months_analyzed=saved.months_analyzed,
            transactions=[
                StatementTxDTO(**tx) for tx in payload.get("transactions", [])
            ],
            transfer_candidates=[
                TransferCandidateDTO(**c)
                for c in payload.get("transfer_candidates", [])
            ],
        )


__all__ = [
    "FinancialCushionService",
    "MAX_PDF_SIZE",
]
