from decimal import Decimal
from typing import List, Optional

from asyncpg import Record

from database.base import PostgresAsyncDatabase
from database.models.expense import Expense, ExpenseCategory, ExpenseOwnerType


class ExpenseRepository:
    """Репозиторий для работы с покупками (расходами) семьи."""

    def __init__(self, db: PostgresAsyncDatabase):
        """
        Инициализация репозитория.

        :param db: Экземпляр базового класса для работы с PostgreSQL.
        """
        self.db = db

    async def add_expense(
        self,
        family_id: int,
        payer_id: int,
        amount: Decimal,
        owner_type: ExpenseOwnerType,
        owner_id: Optional[int],
        category: ExpenseCategory = "other",
    ) -> Expense:
        """
        Добавляет новую покупку.

        :param family_id: Идентификатор семьи.
        :param payer_id: Идентификатор пользователя, который заплатил.
        :param amount: Сумма покупки.
        :param owner_type: Кому принадлежит покупка (self/member/shared).
        :param owner_id: Идентификатор участника-владельца (только для owner_type="member").
        :param category: Категория покупки.
        :return: Созданная покупка.
        """
        expense_row: Record = await self.db.fetchrow(
            """
            INSERT INTO expenses (family_id, payer_id, amount, owner_type, owner_id, category)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, family_id, payer_id, amount, owner_type, owner_id, category, created_at
            """,
            (family_id, payer_id, amount, owner_type, owner_id, category),
        )

        return Expense.model_validate(dict(expense_row))

    async def list_family_expenses(self, family_id: int, limit: int = 50) -> List[Expense]:
        """
        Возвращает последние покупки семьи.

        :param family_id: Идентификатор семьи.
        :param limit: Максимальное количество покупок в ответе.
        :return: Список покупок, отсортированный от новых к старым.
        """
        rows = await self.db.fetch(
            """
            SELECT id, family_id, payer_id, amount, owner_type, owner_id, category, created_at
            FROM expenses
            WHERE family_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            (family_id, limit),
        )

        return [Expense.model_validate(dict(row)) for row in rows]


__all__ = [
    "ExpenseRepository",
]
