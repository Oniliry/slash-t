from __future__ import annotations

import asyncio

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import List, Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency for runtime
    OpenAI = None

from core.config import OPENAI_API_KEY, OPENAI_BASE_URL
from database.models.expense import Expense, ExpenseItem
from database.models.user import User
from database.repositories.debt_repo import DebtRepository
from database.repositories.expense_repo import ExpenseRepository
from database.repositories.user_repo import UserRepository
from logger import logger
from schemas.base import APIResponse
from schemas.notification import NotificationItem


_CATEGORY_TRANSLATIONS = {
    "groceries": "продукты",
    "utilities": "жкх и связь",
    "transport": "транспорт",
    "cafe": "кафе и рестораны",
    "entertainment": "развлечения",
    "health": "здоровье",
    "clothing": "одежда",
    "other": "прочие расходы",
}

_OWNER_TYPE_TRANSLATIONS = {
    "self": "личная покупка",
    "member": "покупка участника семьи",
    "shared": "общая покупка",
}


def _translate_category(value: str | None) -> str:
    value = value or "other"
    return _CATEGORY_TRANSLATIONS.get(value, value)


def _translate_owner_type(value: str | None) -> str:
    value = value or "shared"
    return _OWNER_TYPE_TRANSLATIONS.get(value, value)


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class NotificationService:
    """Генерирует уведомления для главной страницы."""

    def __init__(
        self,
        debt_repo: DebtRepository,
        expense_repo: ExpenseRepository,
        user_repo: UserRepository,
    ) -> None:
        self.debt_repo = debt_repo
        self.expense_repo = expense_repo
        self.user_repo = user_repo

    @staticmethod
    def _money(value: float) -> str:
        return f"{value:,.2f} ₽".replace(",", " ")

    async def get_notifications(self, user: User) -> APIResponse[List[NotificationItem]]:
        """Возвращает список уведомлений для текущего пользователя."""
        notifications: List[NotificationItem] = []

        if user.family_id is None:
            return APIResponse.success(
                data=[
                    NotificationItem(
                        kind="personal",
                        text="Добавьте семью, чтобы видеть общие напоминания и взаиморасчёты.",
                    )
                ],
                message="Уведомления готовы.",
            )

        members = await self.user_repo.get_family_members(user.family_id)
        names = {member.id: member.name for member in members}

        i_owe = await self.debt_repo.list_debts_as_debtor(user.id)
        owed_to_me = await self.debt_repo.list_debts_as_creditor(user.id)

        for debt in i_owe[:3]:
            creditor_name = names.get(debt.creditor_id, "Участник")
            notifications.append(
                NotificationItem(
                    kind="personal",
                    text=f"Вы должны {creditor_name} {self._money(float(debt.amount))}.",
                )
            )

        for debt in owed_to_me[:3]:
            debtor_name = names.get(debt.debtor_id, "Участник")
            notifications.append(
                NotificationItem(
                    kind="personal",
                    text=f"{debtor_name} должен вам {self._money(float(debt.amount))}.",
                )
            )

        recent_expenses = await self.expense_repo.list_family_expenses(user.family_id, limit=100)
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        filtered_expenses = [
            exp
            for exp in recent_expenses
            if _normalize_datetime(exp.created_at) is not None
            and _normalize_datetime(exp.created_at) >= cutoff
        ]

        if filtered_expenses:
            total_amount = sum(float(exp.amount) for exp in filtered_expenses)
            categories = Counter()
            for expense in filtered_expenses:
                categories[expense.category] += 1
            top_category = max(categories.items(), key=lambda item: item[1])[0] if categories else "other"
            notifications.append(
                NotificationItem(
                    kind="family",
                    text=(
                        f"За месяц семья потратила {self._money(total_amount)} на "
                        f"{len(filtered_expenses)} покупок. Самая частая категория — "
                        f"{_translate_category(top_category)}."
                    ),
                )
            )

        personal_items = self._personal_expense_items(filtered_expenses, user.id)
        if personal_items:
            personal_total = sum(float(item.sum) for item in personal_items)
            categories = Counter(item.category for item in personal_items)
            top_category = max(categories.items(), key=lambda item: item[1])[0] if categories else "other"
            notifications.append(
                NotificationItem(
                    kind="personal",
                    text=(
                        f"Ваши личные траты за месяц составили {self._money(personal_total)}. "
                        f"Чаще всего вы покупали: {_translate_category(top_category)}."
                    ),
                )
            )

        if not notifications:
            notifications.append(
                NotificationItem(
                    kind="family",
                    text="Пока нет активных долгов и покупок. Хороший момент проверить семейный бюджет.",
                )
            )

        return APIResponse.success(data=notifications[:6], message="Уведомления загружены.")

    async def get_ai_advice(self, user: User) -> APIResponse[NotificationItem]:
        """Генерирует AI-совет отдельным запросом, не задерживая страницу."""
        if user.family_id is None:
            return APIResponse.success(
                data=NotificationItem(kind="advice", text="Ошибка нейросети: пользователь не добавлен в семью."),
                message="AI-уведомление недоступно.",
            )

        recent_expenses = await self.expense_repo.list_family_expenses(user.family_id, limit=100)
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        filtered_expenses = [
            expense
            for expense in recent_expenses
            if _normalize_datetime(expense.created_at) is not None
            and _normalize_datetime(expense.created_at) >= cutoff
        ]
        personal_items = self._personal_expense_items(filtered_expenses, user.id)
        advice = await self._generate_ai_advice(user, filtered_expenses, personal_items)
        return APIResponse.success(
            data=NotificationItem(kind="advice", text=advice or "Ошибка нейросети: пустой ответ."),
            message="AI-уведомление готово.",
        )

    @staticmethod
    def _personal_expense_items(expenses: List[Expense], user_id: int) -> List[ExpenseItem]:
        items: List[ExpenseItem] = []
        for expense in expenses:
            expense_items = expense.items if hasattr(expense, "items") else []
            if expense_items:
                for item in expense_items:
                    is_personal = (
                        (item.owner_type == "member" and item.owner_id == user_id)
                        or (item.owner_type == "self" and expense.payer_id == user_id)
                    )
                    if is_personal:
                        items.append(item)
        return items

    async def _generate_ai_advice(
        self,
        user: User,
        recent_expenses: List[Expense],
        personal_items: List[ExpenseItem],
    ) -> Optional[str]:
        if not OPENAI_API_KEY:
            logger.warning("OpenAI disabled: OPENAI_API_KEY is not configured")
            return "Ошибка нейросети: не задан ключ OPENAI_API_KEY"
        if OpenAI is None:
            logger.warning("OpenAI disabled: SDK is not installed")
            return "Ошибка нейросети: не установлен пакет openai"

        family_total = sum(float(exp.amount) for exp in recent_expenses)
        personal_total = sum(float(item.sum) for item in personal_items)
        family_top = []
        for expense in recent_expenses:
            family_top.append(f"{_translate_category(expense.category)}: {float(expense.amount):.2f}")

        expense_context = []
        for expense in recent_expenses:
            item_lines = []
            if hasattr(expense, "items") and expense.items:
                for item in expense.items:
                    item_lines.append(
                        f"- {item.name}: {float(item.sum):.2f} ₽, "
                        f"категория={_translate_category(item.category)}, "
                        f"тип покупки={_translate_owner_type(item.owner_type)}"
                    )
            else:
                item_lines.append(
                    f"- покупка: {float(expense.amount):.2f} ₽, "
                    f"категория={_translate_category(expense.category)}, "
                    f"тип покупки={_translate_owner_type(expense.owner_type)}"
                )
            expense_context.append(
                f"Покупка {expense.id}: магазин={expense.shop_name or 'не указано'}, сумма={float(expense.amount):.2f} ₽; "
                + ("\n".join(item_lines))
            )

        try:
            client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, timeout=20.0)
            prompt = (
                "Сделай короткий финансовый совет для пользователя семьи на основе реальных данных о покупках. "
                f"Личные траты за месяц: {personal_total:.2f} ₽. "
                f"Семейные траты за месяц: {family_total:.2f} ₽. "
                f"Важные категории: {', '.join(family_top[:5]) or 'нет данных'}. "
                "Вот все последние покупки семьи: "
                + " | ".join(expense_context[:8])
                + ". "
                "Сделай вывод о том, куда уходит больше денег, где можно сократить траты, и как лучше распределить бюджет. "
                "Ответь одним коротким абзацем в 1-2 предложения, по-русски, без markdown."
            )
            logger.info("Sending OpenAI advice request for user_id=%s, recent_expenses=%s", user.id, len(recent_expenses))
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="openai/gpt-5-nano",
                messages=[
                    {"role": "system", "content": "Ты финансовый советник. Отвечай кратко и по делу."},
                    {"role": "user", "content": prompt},
                ],
            )
            text = (response.choices[0].message.content or "").strip()
            if not text:
                logger.warning("OpenAI returned empty response for user_id=%s", user.id)
                return "Ошибка нейросети: нейросеть вернула пустой ответ"
            return text
        except Exception as exc:
            logger.exception("OpenAI advice generation failed for user_id=%s", user.id)
            error_text = str(exc).strip() or exc.__class__.__name__
            return f"Ошибка нейросети: {error_text}"


__all__ = [
    "NotificationService",
]
