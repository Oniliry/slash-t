from decimal import Decimal
from typing import List, Optional

from asyncpg import Record

from database.base import PostgresAsyncDatabase
from database.models.cushion import CushionGoal, CushionOperation, CushionOperationKind


class CushionRepository:
    """Репозиторий финансовой подушки семьи: операции и цель накоплений."""

    def __init__(self, db: PostgresAsyncDatabase):
        """
        Инициализация репозитория.

        :param db: Экземпляр базового класса для работы с PostgreSQL.
        """
        self.db = db

    async def add_operation(
        self,
        family_id: int,
        user_id: int,
        kind: CushionOperationKind,
        amount: Decimal,
        comment: Optional[str] = None,
    ) -> CushionOperation:
        """
        Добавляет операцию пополнения или списания из подушки.

        :param family_id: Идентификатор семьи.
        :param user_id: Идентификатор пользователя, совершившего операцию.
        :param kind: Тип операции: topup (пополнение) или withdraw (списание).
        :param amount: Сумма операции (положительная).
        :param comment: Комментарий к операции.
        :return: Созданная операция.
        """
        row: Record = await self.db.fetchrow(
            """
            INSERT INTO cushion_operations (family_id, user_id, kind, amount, comment)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, family_id, user_id, kind, amount, comment, created_at
            """,
            (family_id, user_id, kind, amount, comment),
        )
        return CushionOperation.model_validate(dict(row))

    async def list_operations(
        self,
        family_id: int,
        limit: int = 50,
    ) -> List[CushionOperation]:
        """
        Возвращает историю операций с подушкой семьи — от новых к старым.

        :param family_id: Идентификатор семьи.
        :param limit: Максимальное количество операций в ответе.
        :return: Список операций.
        """
        rows = await self.db.fetch(
            """
            SELECT id, family_id, user_id, kind, amount, comment, created_at
            FROM cushion_operations
            WHERE family_id = $1
            ORDER BY created_at DESC, id DESC
            LIMIT $2
            """,
            (family_id, limit),
        )
        return [CushionOperation.model_validate(dict(row)) for row in rows]

    async def get_balance(self, family_id: int) -> Decimal:
        """
        Считает текущий размер подушки семьи: сумма пополнений минус списания.

        :param family_id: Идентификатор семьи.
        :return: Текущий баланс подушки (может быть нулевым).
        """
        row: Optional[Record] = await self.db.fetchrow(
            """
            SELECT
                COALESCE(SUM(amount) FILTER (WHERE kind = 'topup'), 0)
                - COALESCE(SUM(amount) FILTER (WHERE kind = 'withdraw'), 0)
                AS balance
            FROM cushion_operations
            WHERE family_id = $1
            """,
            (family_id,),
        )
        return Decimal(str(row["balance"])) if row else Decimal("0")

    async def get_goal(self, family_id: int) -> Optional[CushionGoal]:
        """
        Возвращает цель по подушке семьи, если она установлена.

        :param family_id: Идентификатор семьи.
        :return: Цель или None, если цель ещё не задана.
        """
        row: Optional[Record] = await self.db.fetchrow(
            """
            SELECT family_id, target_amount, months, updated_at
            FROM cushion_goals
            WHERE family_id = $1
            """,
            (family_id,),
        )
        return CushionGoal.model_validate(dict(row)) if row else None

    async def upsert_goal(
        self,
        family_id: int,
        target_amount: Decimal,
        months: int,
    ) -> CushionGoal:
        """
        Создаёт или обновляет цель по подушке семьи.

        :param family_id: Идентификатор семьи.
        :param target_amount: Целевая сумма.
        :param months: На сколько месяцев расходов рассчитана подушка.
        :return: Сохранённая цель.
        """
        row: Record = await self.db.fetchrow(
            """
            INSERT INTO cushion_goals (family_id, target_amount, months)
            VALUES ($1, $2, $3)
            ON CONFLICT (family_id)
            DO UPDATE SET target_amount = EXCLUDED.target_amount,
                          months = EXCLUDED.months,
                          updated_at = now()
            RETURNING family_id, target_amount, months, updated_at
            """,
            (family_id, target_amount, months),
        )
        return CushionGoal.model_validate(dict(row))


__all__ = [
    "CushionRepository",
]
