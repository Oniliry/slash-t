from decimal import Decimal
from typing import List, Optional

from asyncpg import Record

from database.base import PostgresAsyncDatabase
from database.models.expense import Expense, ExpenseCategory, ExpenseItem, ExpenseOwnerType

_EXPENSE_FIELDS = (
    "id, family_id, payer_id, amount, owner_type, owner_id, category, shop_name, created_at"
)


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
        shop_name: Optional[str] = None,
    ) -> Expense:
        """
        Добавляет новую покупку.

        :param family_id: Идентификатор семьи.
        :param payer_id: Идентификатор пользователя, который заплатил.
        :param amount: Сумма покупки.
        :param owner_type: Кому принадлежит покупка (self/member/shared).
        :param owner_id: Идентификатор участника-владельца (только для owner_type="member").
        :param category: Категория покупки.
        :param shop_name: Название покупки (например, магазин с чека).
        :return: Созданная покупка.
        """
        expense_row: Record = await self.db.fetchrow(
            f"""
            INSERT INTO expenses (family_id, payer_id, amount, owner_type, owner_id, category, shop_name)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING {_EXPENSE_FIELDS}
            """,
            (family_id, payer_id, amount, owner_type, owner_id, category, shop_name),
        )

        return Expense.model_validate(dict(expense_row))

    async def add_items(
        self,
        expense_id: int,
        items: List[dict],
    ) -> List[ExpenseItem]:
        """
        Добавляет позиции (товары) к уже созданной покупке.

        :param expense_id: Идентификатор покупки.
        :param items: Список словарей с ключами name/sum/category.
        :return: Список созданных позиций в порядке добавления.
        """
        created: List[ExpenseItem] = []
        for position, item in enumerate(items):
            row: Record = await self.db.fetchrow(
                """
                INSERT INTO expense_items (expense_id, name, sum, category, position, owner_type, owner_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, expense_id, name, sum, category, owner_type, owner_id
                """,
                (
                    expense_id,
                    item["name"],
                    item["sum"],
                    item.get("category", "other"),
                    position,
                    item.get("owner_type", "shared"),
                    item.get("owner_id"),
                ),
            )
            created.append(ExpenseItem.model_validate(dict(row)))

        return created

    async def get_items(self, expense_id: int) -> List[ExpenseItem]:
        """
        Возвращает позиции покупки в порядке добавления.

        :param expense_id: Идентификатор покупки.
        :return: Список позиций покупки.
        """
        rows = await self.db.fetch(
            """
            SELECT id, expense_id, name, sum, category, owner_type, owner_id
            FROM expense_items
            WHERE expense_id = $1
            ORDER BY position ASC, id ASC
            """,
            (expense_id,),
        )
        return [ExpenseItem.model_validate(dict(row)) for row in rows]

    async def get_expense(self, expense_id: int) -> Optional[Expense]:
        """
        Возвращает покупку по идентификатору.

        :param expense_id: Идентификатор покупки.
        :return: Покупка или None, если не найдена.
        """
        row = await self.db.fetchrow(
            f"""
            SELECT {_EXPENSE_FIELDS}
            FROM expenses
            WHERE id = $1
            """,
            (expense_id,),
        )
        return Expense.model_validate(dict(row)) if row else None

    async def list_family_expenses(self, family_id: int, limit: int = 50) -> List[Expense]:
        """
        Возвращает последние покупки семьи.

        :param family_id: Идентификатор семьи.
        :param limit: Максимальное количество покупок в ответе.
        :return: Список покупок, отсортированный от новых к старым.
        """
        rows = await self.db.fetch(
            f"""
            SELECT {_EXPENSE_FIELDS}
            FROM expenses
            WHERE family_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            (family_id, limit),
        )

        return [Expense.model_validate(dict(row)) for row in rows]

    async def count_items(self, expense_ids: List[int]) -> dict:
        """
        Считает количество позиций для набора покупок одним запросом.

        :param expense_ids: Список идентификаторов покупок.
        :return: Словарь {expense_id: количество позиций}.
        """
        if not expense_ids:
            return {}

        rows = await self.db.fetch(
            """
            SELECT expense_id, COUNT(*) AS items_count
            FROM expense_items
            WHERE expense_id = ANY($1)
            GROUP BY expense_id
            """,
            (expense_ids,),
        )
        return {row["expense_id"]: row["items_count"] for row in rows}


__all__ = [
    "ExpenseRepository",
]
