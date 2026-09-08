from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List

from database.models.user import User
from database.repositories.cushion_repo import CushionRepository
from database.repositories.expense_repo import ExpenseRepository
from database.repositories.user_repo import UserRepository
from schemas.base import APIResponse
from schemas.cushion import (
    CushionGoalResponse,
    CushionOperationRequest,
    CushionOperationResponse,
    CushionStateResponse,
    SetCushionGoalRequest,
)


class CushionService:
    """Сервис финансовой подушки семьи: баланс, цель, операции."""

    def __init__(
        self,
        cushion_repo: CushionRepository,
        expense_repo: ExpenseRepository,
        user_repo: UserRepository,
    ):
        """
        Инициализация сервиса.

        :param cushion_repo: Репозиторий операций и цели подушки.
        :param expense_repo: Репозиторий покупок (для ориентира расходов).
        :param user_repo: Репозиторий пользователей (для имён в истории).
        """
        self.cushion_repo = cushion_repo
        self.expense_repo = expense_repo
        self.user_repo = user_repo

    async def get_state(self, user: User) -> APIResponse:
        """
        Возвращает состояние подушки семьи: баланс, цель, прогресс
        и историю операций.

        :param user: Текущий авторизованный пользователь.
        :return: Состояние подушки или ошибка family_required.
        """
        if user.family_id is None:
            return APIResponse.fail(
                message="Сначала создайте семью или присоединитесь к ней.",
                status_code=403,
                type="family_required",
            )

        balance = await self.cushion_repo.get_balance(user.family_id)
        operations = await self.cushion_repo.list_operations(user.family_id)
        goal = await self.cushion_repo.get_goal(user.family_id)

        members = await self.user_repo.get_family_members(user.family_id)
        names: Dict[int, str] = {member.id: member.name for member in members}

        monthly_expenses = await self._monthly_expenses_avg(user.family_id)

        goal_response = None
        if goal is not None:
            progress = (
                int(
                    (Decimal(balance) / goal.target_amount * 100)
                    .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                )
                if goal.target_amount > 0
                else 0
            )
            goal_response = CushionGoalResponse(
                target_amount=goal.target_amount,
                months=goal.months,
                progress_percent=max(0, min(progress, 100)),
            )

        operation_responses = [
            CushionOperationResponse(
                id=operation.id,
                kind=operation.kind,
                amount=operation.amount,
                comment=operation.comment,
                user_name=names.get(operation.user_id),
                created_at=operation.created_at,
            )
            for operation in operations
        ]

        return APIResponse.success(
            CushionStateResponse(
                balance=balance,
                monthly_expenses=monthly_expenses,
                goal=goal_response,
                operations=operation_responses,
            )
        )

    async def top_up(self, user: User, data: CushionOperationRequest) -> APIResponse:
        """
        Пополняет финансовую подушку семьи.

        :param user: Текущий авторизованный пользователь.
        :param data: Сумма и комментарий.
        :return: Обновлённое состояние подушки или ошибка family_required.
        """
        return await self._add_operation(user, "topup", data)

    async def withdraw(self, user: User, data: CushionOperationRequest) -> APIResponse:
        """
        Списывает средства из финансовой подушки семьи.

        :param user: Текущий авторизованный пользователь.
        :param data: Сумма и комментарий.
        :return: Обновлённое состояние подушки, ошибку family_required
            или ошибку недостаточно средств.
        """
        balance = await self.cushion_repo.get_balance(user.family_id) if user.family_id else Decimal("0")
        if user.family_id is None:
            return APIResponse.fail(
                message="Сначала создайте семью или присоединитесь к ней.",
                status_code=403,
                type="family_required",
            )
        if balance < data.amount:
            return APIResponse.fail(
                message="Недостаточно средств в подушке.",
                status_code=400,
                type="insufficient_funds",
            )
        return await self._add_operation(user, "withdraw", data)

    async def set_goal(self, user: User, data: SetCushionGoalRequest) -> APIResponse:
        """
        Устанавливает или обновляет цель по подушке семьи.

        :param user: Текущий авторизованный пользователь.
        :param data: Целевая сумма и число месяцев.
        :return: Обновлённое состояние подушки или ошибка family_required.
        """
        if user.family_id is None:
            return APIResponse.fail(
                message="Сначала создайте семью или присоединитесь к ней.",
                status_code=403,
                type="family_required",
            )

        await self.cushion_repo.upsert_goal(
            user.family_id, data.target_amount, data.months
        )
        return await self.get_state(user)

    async def _add_operation(
        self,
        user: User,
        kind: str,
        data: CushionOperationRequest,
    ) -> APIResponse:
        """
        Общая логика добавления операции (пополнение или списание).

        :param user: Текущий авторизованный пользователь.
        :param kind: Тип операции: topup или withdraw.
        :param data: Сумма и комментарий.
        :return: Обновлённое состояние подушки или ошибка family_required.
        """
        if user.family_id is None:
            return APIResponse.fail(
                message="Сначала создайте семью или присоединитесь к ней.",
                status_code=403,
                type="family_required",
            )

        await self.cushion_repo.add_operation(
            user.family_id, user.id, kind, data.amount, data.comment
        )
        return await self.get_state(user)

    async def _monthly_expenses_avg(self, family_id: int) -> Decimal:
        """
        Считает средние расходы семьи в месяц за последние 3 месяца.

        Подсказка пользователю, сколько должна стоить подушка:
        классически это 3–6 месяцев обычных расходов семьи.

        :param family_id: Идентификатор семьи.
        :return: Средние расходы за месяц (0, если покупок нет).
        """
        expenses = await self.expense_repo.list_family_expenses(family_id, limit=500)

        by_month: Dict[str, Decimal] = {}
        for expense in expenses:
            key = expense.created_at.strftime("%Y-%m")
            by_month[key] = by_month.get(key, Decimal("0")) + expense.amount

        if not by_month:
            return Decimal("0")

        recent = sorted(by_month.keys(), reverse=True)[:3]
        total = sum((by_month[key] for key in recent), Decimal("0"))
        return (total / len(recent)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


__all__ = [
    "CushionService",
]
