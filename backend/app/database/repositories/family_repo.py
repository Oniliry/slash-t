from typing import Optional

from asyncpg import Record

from database.base import PostgresAsyncDatabase
from database.models.family import Family


class FamilyRepository:
    """Репозиторий для работы с семейными пространствами."""

    def __init__(self, db: PostgresAsyncDatabase):
        """
        Инициализация репозитория.

        :param db: Экземпляр базового класса для работы с PostgreSQL.
        """
        self.db = db

    async def add_family(self, name: str, invite_code: str, created_by: int) -> Family:
        """
        Создаёт новую семью.

        :param name: Название семьи, придуманное создателем.
        :param invite_code: Уникальный код приглашения для входа в семью.
        :param created_by: Идентификатор пользователя-создателя.
        :return: Созданная семья.
        """
        family_row: Record = await self.db.fetchrow(
            """
            INSERT INTO families (name, invite_code, created_by)
            VALUES ($1, $2, $3)
            RETURNING id, name, invite_code, created_by, created_at
            """,
            (name, invite_code, created_by),
        )

        return Family.model_validate(dict(family_row))

    async def get_family_by_invite_code(self, invite_code: str) -> Optional[Family]:
        """
        Находит семью по коду приглашения.

        :param invite_code: Код приглашения семьи.
        :return: Семья или None, если код недействителен.
        """
        family_row: Optional[Record] = await self.db.fetchrow(
            """
            SELECT id, name, invite_code, created_by, created_at
            FROM families
            WHERE invite_code = $1
            """,
            (invite_code,),
        )

        if family_row is None:
            return None

        return Family.model_validate(dict(family_row))

    async def get_family(self, family_id: int) -> Optional[Family]:
        """
        Получает семью по идентификатору.

        :param family_id: Уникальный идентификатор семьи.
        :return: Семья или None, если она не найдена.
        """
        family_row: Optional[Record] = await self.db.fetchrow(
            """
            SELECT id, name, invite_code, created_by, created_at
            FROM families
            WHERE id = $1
            """,
            (family_id,),
        )

        if family_row is None:
            return None

        return Family.model_validate(dict(family_row))

    async def invite_code_exists(self, invite_code: str) -> bool:
        """
        Проверяет, занят ли код приглашения другой семьёй.

        :param invite_code: Проверяемый код приглашения.
        :return: True, если код уже используется.
        """
        value = await self.db.fetchval(
            """
            SELECT EXISTS(SELECT 1 FROM families WHERE invite_code = $1)
            """,
            (invite_code,),
        )
        return bool(value)

    async def rename_family(self, family_id: int, name: str) -> Optional[Family]:
        """
        Меняет название семьи.

        :param family_id: Уникальный идентификатор семьи.
        :param name: Новое название семьи.
        :return: Обновлённая семья или None, если она не найдена.
        """
        family_row: Optional[Record] = await self.db.fetchrow(
            """
            UPDATE families
            SET name = $2
            WHERE id = $1
            RETURNING id, name, invite_code, created_by, created_at
            """,
            (family_id, name),
        )

        if family_row is None:
            return None

        return Family.model_validate(dict(family_row))

    async def delete_family(self, family_id: int, created_by: int) -> bool:
        """Удаляет семью, если её создатель остаётся единственным участником."""
        deleted_id = await self.db.fetchval(
            """
            DELETE FROM families
            WHERE id = $1
              AND created_by = $2
              AND NOT EXISTS (
                  SELECT 1
                  FROM users
                  WHERE family_id = $1 AND id <> $2
              )
            RETURNING id
            """,
            (family_id, created_by),
        )
        return deleted_id is not None


__all__ = [
    "FamilyRepository",
]
