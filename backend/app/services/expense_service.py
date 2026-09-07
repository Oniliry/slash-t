from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List, Optional

from database.models.debt import Debt
from database.models.expense import Expense
from database.models.user import User
from database.repositories.debt_repo import DebtRepository
from database.repositories.expense_repo import ExpenseRepository
from database.repositories.family_repo import FamilyRepository
from database.repositories.user_repo import UserRepository
from schemas.base import APIResponse
from schemas.expense import (
    CreateExpenseRequest,
    DebtParticipantResponse,
    DebtResponse,
    ExpenseItemResponse,
    ExpenseResponse,
    MyDebtsResponse,
)

_CENTS = Decimal("0.01")


class ExpenseService:
    """Сервис добавления покупок и распределения долгов между членами семьи."""

    def __init__(
        self,
        expense_repo: ExpenseRepository,
        debt_repo: DebtRepository,
        family_repo: FamilyRepository,
        user_repo: UserRepository,
    ):
        """
        Инициализация сервиса.

        :param expense_repo: Репозиторий покупок.
        :param debt_repo: Репозиторий долгов.
        :param family_repo: Репозиторий семей.
        :param user_repo: Репозиторий пользователей.
        """
        self.expense_repo = expense_repo
        self.debt_repo = debt_repo
        self.family_repo = family_repo
        self.user_repo = user_repo

    @staticmethod
    def _income_shares(members: List[User]) -> Dict[int, Decimal]:
        """
        Считает долю каждого взрослого участника в общем доходе семьи.

        Логика полностью повторяет расчёт доли бюджета в FamilyService:
        доля взрослого — это его доход, делённый на суммарный доход всех
        взрослых семьи. У детей доли нет (они неплатежеспособны).

        :param members: Список участников семьи.
        :return: Словарь {user_id: доля от 0 до 1} только для взрослых с доходом.
        """
        total_income = sum(
            (member.monthly_income for member in members if member.role == "adult" and member.monthly_income),
            Decimal("0"),
        )

        if total_income <= 0:
            return {}

        return {
            member.id: member.monthly_income / total_income
            for member in members
            if member.role == "adult" and member.monthly_income
        }

    def _debt_response(self, debt: Debt, names: Dict[int, str]) -> DebtResponse:
        """
        Собирает ответ по долгу вместе с именами должника и получателя.

        :param debt: Модель долга.
        :param names: Словарь {user_id: имя} участников семьи.
        :return: Схема ответа с данными долга.
        """
        return DebtResponse(
            id=debt.id,
            expense_id=debt.expense_id,
            amount=debt.amount,
            status=debt.status,
            created_at=debt.created_at,
            confirmed_at=debt.confirmed_at,
            debtor=DebtParticipantResponse(id=debt.debtor_id, name=names.get(debt.debtor_id, "Участник")),
            creditor=DebtParticipantResponse(id=debt.creditor_id, name=names.get(debt.creditor_id, "Участник")),
        )

    async def _net_debts_between(
        self,
        family_id: int,
        expense_id: int,
        debtor_id: int,
        creditor_id: int,
        new_debt: Debt,
    ) -> Optional[Debt]:
        """
        Проверяет, нет ли встречного долга между теми же двумя участниками,
        и если есть — взаимозачитывает все непогашенные долги между ними,
        оставляя одним долгом только чистую разницу.

        Например: человек1 уже должен человеку2 1000 ₽, а теперь возник
        новый долг человека2 перед человеком1 на 2000 ₽. Вместо двух долгов
        останется один: человек2 должен человеку1 1000 ₽.

        :param family_id: Идентификатор семьи.
        :param expense_id: Покупка, к которой будет привязан итоговый долг.
        :param debtor_id: Должник по только что созданному долгу.
        :param creditor_id: Получатель по только что созданному долгу.
        :param new_debt: Только что созданный долг (возвращается как есть,
            если взаимозачитывать не с чем).
        :return: Итоговый долг после взаимозачёта или None, если долги
            между участниками полностью погасили друг друга.
        """
        pending = await self.debt_repo.list_pending_between(family_id, debtor_id, creditor_id)

        forward = [d for d in pending if d.debtor_id == debtor_id and d.creditor_id == creditor_id]
        backward = [d for d in pending if d.debtor_id == creditor_id and d.creditor_id == debtor_id]

        if not backward:
            # Встречных долгов нет — взаимозачитывать нечего.
            return new_debt

        total_forward = sum((d.amount for d in forward), Decimal("0"))
        total_backward = sum((d.amount for d in backward), Decimal("0"))

        await self.debt_repo.mark_netted([d.id for d in forward] + [d.id for d in backward])

        net_amount = (total_forward - total_backward).quantize(_CENTS, rounding=ROUND_HALF_UP)

        if net_amount == 0:
            return None

        if net_amount > 0:
            return await self.debt_repo.add_debt(
                expense_id=expense_id,
                family_id=family_id,
                debtor_id=debtor_id,
                creditor_id=creditor_id,
                amount=net_amount,
            )

        return await self.debt_repo.add_debt(
            expense_id=expense_id,
            family_id=family_id,
            debtor_id=creditor_id,
            creditor_id=debtor_id,
            amount=-net_amount,
        )

    @staticmethod
    def _resolve_owner(owner_type, owner_id, user, members_by_id):
        """
        Проверяет и нормализует владельца (покупки целиком или одного товара):
        покупка "для себя" всегда превращается в self, ребёнку нельзя
        выставить долг.

        :return: Кортеж (owner_type, owner_id, ошибка или None).
        """
        if owner_type != "member":
            return owner_type, None, None

        owner = members_by_id.get(owner_id)
        if owner is None:
            return None, None, ("Участник не найден в этой семье.", 404, "member_not_found")

        if owner.id == user.id:
            return "self", None, None

        if owner.role == "child":
            return None, None, (
                "Ребёнку нельзя выставить долг — выберите «Общая», "
                "чтобы распределить трату между взрослыми.",
                400,
                "cannot_charge_child",
            )

        return owner_type, owner_id, None

    async def _create_debts_for_owner(
        self, user: User, family_id: int, expense_id: int, owner_type: str, owner_id, amount, members,
    ) -> List[Debt]:
        """Создаёт долги для одной группы покупки/товаров с общим владельцем."""
        debts: List[Debt] = []

        if owner_type == "member":
            debt = await self.debt_repo.add_debt(
                expense_id=expense_id,
                family_id=family_id,
                debtor_id=owner_id,
                creditor_id=user.id,
                amount=amount,
            )
            net_debt = await self._net_debts_between(family_id, expense_id, owner_id, user.id, debt)
            if net_debt is not None:
                debts.append(net_debt)
        elif owner_type == "shared":
            shares = self._income_shares(members)
            for member in members:
                if member.id == user.id:
                    continue
                share = shares.get(member.id)
                if not share:
                    continue

                debt_amount = (amount * share).quantize(_CENTS, rounding=ROUND_HALF_UP)
                if debt_amount <= 0:
                    continue

                debt = await self.debt_repo.add_debt(
                    expense_id=expense_id,
                    family_id=family_id,
                    debtor_id=member.id,
                    creditor_id=user.id,
                    amount=debt_amount,
                )
                net_debt = await self._net_debts_between(family_id, expense_id, member.id, user.id, debt)
                if net_debt is not None:
                    debts.append(net_debt)

        return debts

    def _item_response(self, item, names: Dict[int, str]) -> ExpenseItemResponse:
        """Собирает ответ по товару вместе с именем владельца (для отображения)."""
        owner_name = names.get(item.owner_id) if item.owner_type == "member" else None
        return ExpenseItemResponse(
            id=item.id,
            name=item.name,
            sum=item.sum,
            category=item.category,
            owner_type=item.owner_type,
            owner_id=item.owner_id,
            owner_name=owner_name,
        )

    async def create_expense(
        self,
        user: User,
        data: CreateExpenseRequest,
    ) -> APIResponse[ExpenseResponse]:
        """
        Добавляет покупку и, если она не личная, создаёт соответствующие долги.

        - self — личный расход, долгов не возникает;
        - member — вся сумма ложится долгом на выбранного участника (кроме
          самого плательщика — тогда покупка тоже считается личной);
        - shared — сумма делится между остальными взрослыми пропорционально
          их доле в общем бюджете семьи (столько же процентов от суммы,
          сколько составляет их доля бюджета).

        Если покупка добавлена через чек (передан items) — у каждого товара
        может быть свой владелец (личное/общее), и покупка всё равно
        сохраняется одной записью в истории; долги считаются отдельно по
        каждой группе товаров с одинаковым владельцем.

        :param user: Текущий авторизованный пользователь (плательщик).
        :param data: Сумма покупки и кому она принадлежит.
        :return: Данные покупки вместе со списком созданных долгов или ошибку.
        """
        if user.family_id is None:
            return APIResponse.fail(
                message="Сначала создайте семью или присоединитесь к ней по коду.",
                status_code=409,
                type="family_required",
            )

        members = await self.user_repo.get_family_members(user.family_id)
        members_by_id = {member.id: member for member in members}
        names = {member.id: member.name for member in members}

        debts: List[Debt] = []

        if data.items:
            resolved_items = []
            for item in data.items:
                owner_type, owner_id, err = self._resolve_owner(
                    item.owner_type, item.owner_id, user, members_by_id,
                )
                if err is not None:
                    message, status_code, error_type = err
                    return APIResponse.fail(message=message, status_code=status_code, type=error_type)
                resolved_items.append({**item.model_dump(), "owner_type": owner_type, "owner_id": owner_id})

            owner_keys = {(i["owner_type"], i["owner_id"]) for i in resolved_items}
            expense_owner_type, expense_owner_id = (
                next(iter(owner_keys)) if len(owner_keys) == 1 else ("shared", None)
            )

            expense = await self.expense_repo.add_expense(
                family_id=user.family_id,
                payer_id=user.id,
                amount=data.amount,
                owner_type=expense_owner_type,
                owner_id=expense_owner_id,
                category=data.category,
                shop_name=data.shop_name,
            )

            created_items = await self.expense_repo.add_items(expense.id, resolved_items)
            items = [self._item_response(item, names) for item in created_items]

            groups: Dict[tuple, Decimal] = {}
            for item in resolved_items:
                key = (item["owner_type"], item["owner_id"])
                groups[key] = groups.get(key, Decimal("0")) + item["sum"]

            for (owner_type, owner_id), group_amount in groups.items():
                debts.extend(
                    await self._create_debts_for_owner(
                        user, user.family_id, expense.id, owner_type, owner_id, group_amount, members,
                    )
                )
        else:
            owner_type, owner_id, err = self._resolve_owner(
                data.owner_type, data.owner_id, user, members_by_id,
            )
            if err is not None:
                message, status_code, error_type = err
                return APIResponse.fail(message=message, status_code=status_code, type=error_type)

            expense = await self.expense_repo.add_expense(
                family_id=user.family_id,
                payer_id=user.id,
                amount=data.amount,
                owner_type=owner_type,
                owner_id=owner_id,
                category=data.category,
                shop_name=data.shop_name,
            )
            items = []

            debts = await self._create_debts_for_owner(
                user, user.family_id, expense.id, owner_type, owner_id, data.amount, members,
            )

        return APIResponse.success(
            data=ExpenseResponse(
                id=expense.id,
                amount=expense.amount,
                owner_type=expense.owner_type,
                owner_id=expense.owner_id,
                payer_id=expense.payer_id,
                payer_name=names.get(expense.payer_id),
                category=expense.category,
                shop_name=expense.shop_name,
                items_count=len(items),
                created_at=expense.created_at,
                debts=[self._debt_response(debt, names) for debt in debts],
                items=items,
            ),
            message="Покупка добавлена.",
        )

    async def list_expenses(self, user: User, limit: int = 50) -> APIResponse[List[ExpenseResponse]]:
        """
        Возвращает историю последних покупок семьи текущего пользователя.

        :param user: Текущий авторизованный пользователь.
        :param limit: Максимальное количество покупок в ответе.
        :return: Список покупок, отсортированный от новых к старым, или ошибку.
        """
        if user.family_id is None:
            return APIResponse.fail(
                message="Вы ещё не состоите ни в одной семье.",
                status_code=404,
                type="family_required",
            )

        members = await self.user_repo.get_family_members(user.family_id)
        names = {member.id: member.name for member in members}

        expenses = await self.expense_repo.list_family_expenses(user.family_id, limit=limit)
        items_counts = await self.expense_repo.count_items([expense.id for expense in expenses])

        return APIResponse.success(
            data=[
                ExpenseResponse(
                    id=expense.id,
                    amount=expense.amount,
                    owner_type=expense.owner_type,
                    owner_id=expense.owner_id,
                    payer_id=expense.payer_id,
                    payer_name=names.get(expense.payer_id),
                    category=expense.category,
                    shop_name=expense.shop_name,
                    items_count=items_counts.get(expense.id, 0),
                    created_at=expense.created_at,
                    debts=[],
                )
                for expense in expenses
            ],
            message="История покупок получена.",
        )

    async def get_expense_detail(self, user: User, expense_id: int) -> APIResponse[ExpenseResponse]:
        """
        Возвращает детальную информацию о покупке вместе со списком позиций
        (для открытия карточки покупки по клику в истории).

        :param user: Текущий авторизованный пользователь.
        :param expense_id: Идентификатор покупки.
        :return: Данные покупки с позициями или сообщение об ошибке.
        """
        expense = await self.expense_repo.get_expense(expense_id)
        if expense is None or expense.family_id != user.family_id:
            return APIResponse.fail(
                message="Покупка не найдена.",
                status_code=404,
                type="expense_not_found",
            )

        members = await self.user_repo.get_family_members(user.family_id)
        names = {member.id: member.name for member in members}
        items = await self.expense_repo.get_items(expense_id)

        return APIResponse.success(
            data=ExpenseResponse(
                id=expense.id,
                amount=expense.amount,
                owner_type=expense.owner_type,
                owner_id=expense.owner_id,
                payer_id=expense.payer_id,
                payer_name=names.get(expense.payer_id),
                category=expense.category,
                shop_name=expense.shop_name,
                items_count=len(items),
                created_at=expense.created_at,
                debts=[],
                items=[self._item_response(item, names) for item in items],
            ),
            message="Покупка найдена.",
        )

    async def get_my_debts(self, user: User) -> APIResponse[MyDebtsResponse]:
        """
        Возвращает долги текущего пользователя: те, что должен он, и те,
        что причитаются ему от других участников семьи.

        :param user: Текущий авторизованный пользователь.
        :return: Сводка долгов или сообщение об ошибке.
        """
        if user.family_id is None:
            return APIResponse.fail(
                message="Вы ещё не состоите ни в одной семье.",
                status_code=404,
                type="family_required",
            )

        members = await self.user_repo.get_family_members(user.family_id)
        names = {member.id: member.name for member in members}

        i_owe = await self.debt_repo.list_debts_as_debtor(user.id)
        owed_to_me = await self.debt_repo.list_debts_as_creditor(user.id)

        return APIResponse.success(
            data=MyDebtsResponse(
                i_owe=[self._debt_response(debt, names) for debt in i_owe],
                owed_to_me=[self._debt_response(debt, names) for debt in owed_to_me],
            ),
            message="Долги успешно получены.",
        )

    async def confirm_debt(self, user: User, debt_id: int) -> APIResponse[DebtResponse]:
        """
        Подтверждает погашение долга. Сделать это может только тот участник,
        которому причитается перевод (получатель), — так подтверждение
        нельзя подделать со стороны должника.

        :param user: Текущий авторизованный пользователь.
        :param debt_id: Идентификатор подтверждаемого долга.
        :return: Обновлённые данные долга или сообщение об ошибке.
        """
        debt = await self.debt_repo.get_debt(debt_id)
        if debt is None or debt.family_id != user.family_id:
            return APIResponse.fail(
                message="Долг не найден.",
                status_code=404,
                type="debt_not_found",
            )

        if debt.creditor_id != user.id:
            return APIResponse.fail(
                message="Подтвердить погашение долга может только тот участник, которому он причитается.",
                status_code=403,
                type="creditor_required",
            )

        if debt.status == "confirmed":
            return APIResponse.fail(
                message="Этот долг уже подтверждён как погашенный.",
                status_code=409,
                type="debt_already_confirmed",
            )

        updated_debt: Optional[Debt] = await self.debt_repo.confirm_debt(debt_id)
        members = await self.user_repo.get_family_members(user.family_id)
        names = {member.id: member.name for member in members}

        return APIResponse.success(
            data=self._debt_response(updated_debt, names),
            message="Погашение долга подтверждено.",
        )


__all__ = [
    "ExpenseService",
]
