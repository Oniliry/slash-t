from decimal import Decimal
from typing import List, Optional

from asyncpg import Record

from database.base import PostgresAsyncDatabase
from database.models.debt import Debt


class DebtRepository:
    """Репозиторий для работы с долгами, возникающими из покупок."""

    def __init__(self, db: PostgresAsyncDatabase):
        """
        Инициализация репозитория.

        :param db: Экземпляр базового класса для работы с PostgreSQL.
        """
        self.db = db

    async def add_debt(
        self,
        expense_id: int,
        family_id: int,
        debtor_id: int,
        creditor_id: int,
        amount: Decimal,
    ) -> Debt:
        """
        Создаёт новый долг в статусе "не погашен".

        :param expense_id: Идентификатор покупки, из которой возник долг.
        :param family_id: Идентификатор семьи.
        :param debtor_id: Идентификатор участника, который должен перевести деньги.
        :param creditor_id: Идентификатор участника, которому причитается перевод.
        :param amount: Сумма долга.
        :return: Созданный долг.
        """
        debt_row: Record = await self.db.fetchrow(
            """
            INSERT INTO debts (expense_id, family_id, debtor_id, creditor_id, amount)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, expense_id, family_id, debtor_id, creditor_id, amount,
                      status, created_at, confirmed_at
            """,
            (expense_id, family_id, debtor_id, creditor_id, amount),
        )

        return Debt.model_validate(dict(debt_row))

    async def get_debt(self, debt_id: int) -> Optional[Debt]:
        """
        Получает долг по идентификатору.

        :param debt_id: Уникальный идентификатор долга.
        :return: Долг или None, если он не найден.
        """
        debt_row: Optional[Record] = await self.db.fetchrow(
            """
            SELECT id, expense_id, family_id, debtor_id, creditor_id, amount,
                   status, created_at, confirmed_at
            FROM debts
            WHERE id = $1
            """,
            (debt_id,),
        )

        if debt_row is None:
            return None

        return Debt.model_validate(dict(debt_row))

    async def list_debts_as_debtor(self, user_id: int, status: str = "pending") -> List[Debt]:
        """
        Возвращает долги, где пользователь выступает должником.

        :param user_id: Идентификатор пользователя-должника.
        :param status: Статус долгов, которые нужно вернуть.
        :return: Список долгов, отсортированный от новых к старым.
        """
        rows = await self.db.fetch(
            """
            SELECT id, expense_id, family_id, debtor_id, creditor_id, amount,
                   status, created_at, confirmed_at
            FROM debts
            WHERE debtor_id = $1 AND status = $2
            ORDER BY created_at DESC
            """,
            (user_id, status),
        )

        return [Debt.model_validate(dict(row)) for row in rows]

    async def list_debts_as_creditor(self, user_id: int, status: str = "pending") -> List[Debt]:
        """
        Возвращает долги, где пользователь выступает получателем перевода.

        :param user_id: Идентификатор пользователя-получателя.
        :param status: Статус долгов, которые нужно вернуть.
        :return: Список долгов, отсортированный от новых к старым.
        """
        rows = await self.db.fetch(
            """
            SELECT id, expense_id, family_id, debtor_id, creditor_id, amount,
                   status, created_at, confirmed_at
            FROM debts
            WHERE creditor_id = $1 AND status = $2
            ORDER BY created_at DESC
            """,
            (user_id, status),
        )

        return [Debt.model_validate(dict(row)) for row in rows]

    async def list_pending_between(self, family_id: int, user_a_id: int, user_b_id: int) -> List[Debt]:
        """
        Возвращает все непогашенные долги между двумя участниками семьи
        в обе стороны сразу. Нужно, чтобы найти встречные долги и
        взаимозачесть их в один после появления нового долга.

        :param family_id: Идентификатор семьи.
        :param user_a_id: Идентификатор первого участника.
        :param user_b_id: Идентификатор второго участника.
        :return: Список непогашенных долгов между этими двумя участниками.
        """
        rows = await self.db.fetch(
            """
            SELECT id, expense_id, family_id, debtor_id, creditor_id, amount,
                   status, created_at, confirmed_at
            FROM debts
            WHERE family_id = $1
              AND status = 'pending'
              AND ((debtor_id = $2 AND creditor_id = $3) OR (debtor_id = $3 AND creditor_id = $2))
            """,
            (family_id, user_a_id, user_b_id),
        )

        return [Debt.model_validate(dict(row)) for row in rows]

    async def mark_netted(self, debt_ids: List[int]) -> None:
        """
        Помечает долги как взаимозачтённые: их сумма учтена во встречном
        долге, поэтому отдельно их гасить не нужно.

        :param debt_ids: Идентификаторы долгов, которые нужно зачесть.
        """
        if not debt_ids:
            return

        await self.db.execute(
            """
            UPDATE debts
            SET status = 'netted'
            WHERE id = ANY($1::int[])
            """,
            (debt_ids,),
        )

    async def confirm_debt(self, debt_id: int) -> Optional[Debt]:
        """
        Помечает долг как погашенный (подтверждено получателем перевода).

        :param debt_id: Уникальный идентификатор долга.
        :return: Обновлённый долг или None, если он не найден.
        """
        debt_row: Optional[Record] = await self.db.fetchrow(
            """
            UPDATE debts
            SET status = 'confirmed', confirmed_at = now()
            WHERE id = $1
            RETURNING id, expense_id, family_id, debtor_id, creditor_id, amount,
                      status, created_at, confirmed_at
            """,
            (debt_id,),
        )

        if debt_row is None:
            return None

        return Debt.model_validate(dict(debt_row))


__all__ = [
    "DebtRepository",
]
