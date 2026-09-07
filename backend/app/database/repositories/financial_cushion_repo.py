import json
from decimal import Decimal
from typing import List, Optional

from asyncpg import Record

from database.base import PostgresAsyncDatabase
from database.models.financial_cushion import CushionAnalysis


class CushionAnalysisRepository:
    """Репозиторий анализа выписок: последний расчёт финподушки участника."""

    def __init__(self, db: PostgresAsyncDatabase):
        """
        Инициализация репозитория.

        :param db: Экземпляр базового класса для работы с PostgreSQL.
        """
        self.db = db

    async def upsert_analysis(
        self,
        user_id: int,
        family_id: int,
        months_analyzed: int,
        cushion_total: Decimal,
        full_months: List[str],
        excluded_months: List[str],
        payload: dict,
    ) -> CushionAnalysis:
        """
        Сохраняет или обновляет последний анализ выписки пользователя.

        :param user_id: Идентификатор пользователя (запись одна на него).
        :param family_id: Идентификатор семьи пользователя.
        :param months_analyzed: Число полных месяцев в расчёте.
        :param cushion_total: Итоговая сумма подушки.
        :param full_months: Подписи полных месяцев.
        :param excluded_months: Подписи отброшенных частичных месяцев.
        :param payload: Полный JSON результата analyze_statement.
        :return: Сохранённый анализ.
        """
        row: Record = await self.db.fetchrow(
            """
            INSERT INTO cushion_analysis (
                user_id, family_id, months_analyzed, cushion_total,
                full_months, excluded_months, payload
            )
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7::jsonb)
            ON CONFLICT (user_id)
            DO UPDATE SET family_id = EXCLUDED.family_id,
                          months_analyzed = EXCLUDED.months_analyzed,
                          cushion_total = EXCLUDED.cushion_total,
                          full_months = EXCLUDED.full_months,
                          excluded_months = EXCLUDED.excluded_months,
                          payload = EXCLUDED.payload,
                          updated_at = now()
            RETURNING user_id, family_id, months_analyzed, cushion_total,
                      full_months, excluded_months, payload, updated_at
            """,
            (
                user_id,
                family_id,
                months_analyzed,
                cushion_total,
                json.dumps(full_months, ensure_ascii=False),
                json.dumps(excluded_months, ensure_ascii=False),
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        return self._to_model(row)

    async def update_cushion_total(
        self,
        user_id: int,
        cushion_total: Decimal,
        payload: Optional[dict] = None,
    ) -> None:
        """
        Обновляет итог пересчёта (и, опционально, правки пользователя
        в транзакциях) без повторного разбора PDF.

        :param user_id: Идентификатор пользователя.
        :param cushion_total: Пересчитанная сумма подушки.
        :param payload: Обновлённый JSON (например, с новыми флагами).
        """
        if payload is None:
            await self.db.execute(
                """
                UPDATE cushion_analysis
                SET cushion_total = $2, updated_at = now()
                WHERE user_id = $1
                """,
                (user_id, cushion_total),
            )
        else:
            await self.db.execute(
                """
                UPDATE cushion_analysis
                SET cushion_total = $2, payload = $3::jsonb, updated_at = now()
                WHERE user_id = $1
                """,
                (user_id, cushion_total, json.dumps(payload, ensure_ascii=False)),
            )

    async def get_user_analysis(self, user_id: int) -> Optional[CushionAnalysis]:
        """
        Возвращает последний анализ выписки пользователя, если он есть.

        :param user_id: Идентификатор пользователя.
        :return: Анализ или None, если пользователь ещё не загружал выписку.
        """
        row: Optional[Record] = await self.db.fetchrow(
            """
            SELECT user_id, family_id, months_analyzed, cushion_total,
                   full_months, excluded_months, payload, updated_at
            FROM cushion_analysis
            WHERE user_id = $1
            """,
            (user_id,),
        )
        return self._to_model(row) if row else None

    async def get_family_summary(self, family_id: int) -> List[dict]:
        """
        Возвращает рейтинг участников семьи по убыванию финподушки.

        Участники без загруженной выписки получают cushion_total = 0.

        :param family_id: Идентификатор семьи.
        :return: Список словарей user_id/user_name/cushion_total/months_analyzed.
        """
        rows = await self.db.fetch(
            """
            SELECT u.id AS user_id,
                   u.name AS user_name,
                   COALESCE(ca.cushion_total, 0) AS cushion_total,
                   ca.months_analyzed
            FROM users u
            LEFT JOIN cushion_analysis ca ON ca.user_id = u.id
            WHERE u.family_id = $1
            ORDER BY cushion_total DESC, u.name
            """,
            (family_id,),
        )
        return [dict(row) for row in rows]

    async def delete_analysis(self, user_id: int) -> None:
        """
        Удаляет сохранённый анализ пользователя (сброс результата).

        :param user_id: Идентификатор пользователя.
        """
        await self.db.execute(
            """
            DELETE FROM cushion_analysis
            WHERE user_id = $1
            """,
            (user_id,),
        )

    @staticmethod
    def _to_model(row: Record) -> CushionAnalysis:
        """Record -> CushionAnalysis (JSONB приходит строкой из asyncpg)."""
        data = dict(row)
        for field in ("full_months", "excluded_months", "payload"):
            value = data.get(field)
            if isinstance(value, str):
                data[field] = json.loads(value)
        return CushionAnalysis.model_validate(data)


__all__ = [
    "CushionAnalysisRepository",
]
