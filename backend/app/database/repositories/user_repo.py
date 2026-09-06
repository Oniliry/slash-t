from decimal import Decimal
from typing import List, Optional

from asyncpg import Record

from database.base import PostgresAsyncDatabase
from database.models.user import User, UserRole


class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, db: PostgresAsyncDatabase):
        """
        Инициализация репозитория.

        :param db: Экземпляр базового класса для работы с PostgreSQL.
        """
        self.db = db

    async def add_user(
        self,
        name: str,
        login: str,
        password_hash: str,
    ) -> User:
        """
        Добавляет нового пользователя.

        :param name: Имя пользователя.
        :param login: Уникальный логин пользователя.
        :param password_hash: Хэш пароля пользователя.
        :return: Созданный пользователь без хэша пароля.
        """
        user_row: Record = await self.db.fetchrow(
            """
            INSERT INTO users (name, login, password_hash)
            VALUES ($1, $2, $3)
            RETURNING id, name, login, created_at, family_id, role, monthly_income
            """,
            (name, login, password_hash),
        )

        return User.model_validate(dict(user_row))

    async def get_user_by_login(self, login: str) -> Optional[Record]:
        """
        Находит пользователя по логину вместе с хэшем пароля.

        :param login: Логин пользователя.
        :return: Запись пользователя или None, если пользователь не найден.
        """
        return await self.db.fetchrow(
            """
            SELECT id, name, login, password_hash, created_at, family_id, role, monthly_income
            FROM users
            WHERE login = $1
            """,
            (login,),
        )

    async def get_user(self, user_id: int) -> Optional[User]:
        """
        Получает публичные данные пользователя по идентификатору.

        :param user_id: Уникальный идентификатор пользователя.
        :return: Модель пользователя или None, если пользователь не найден.
        """
        user_row: Optional[Record] = await self.db.fetchrow(
            """
            SELECT id, name, login, created_at, family_id, role, monthly_income
            FROM users
            WHERE id = $1
            """,
            (user_id,),
        )

        if user_row is None:
            return None

        return User.model_validate(dict(user_row))

    async def set_user_family(self, user_id: int, family_id: int) -> Optional[User]:
        """
        Привязывает пользователя к семье (при создании или входе по коду).

        :param user_id: Уникальный идентификатор пользователя.
        :param family_id: Идентификатор семьи, к которой присоединяется пользователь.
        :return: Обновлённая модель пользователя или None, если пользователь не найден.
        """
        user_row: Optional[Record] = await self.db.fetchrow(
            """
            UPDATE users
            SET family_id = $2
            WHERE id = $1
            RETURNING id, name, login, created_at, family_id, role, monthly_income
            """,
            (user_id, family_id),
        )

        if user_row is None:
            return None

        return User.model_validate(dict(user_row))

    async def set_user_role(
        self,
        user_id: int,
        role: UserRole,
        monthly_income: Optional[Decimal],
    ) -> Optional[User]:
        """
        Сохраняет выбранную роль пользователя в семье и его доход.

        :param user_id: Уникальный идентификатор пользователя.
        :param role: Роль в семье: adult (взрослый) или child (ребёнок).
        :param monthly_income: Примерный месячный доход (только для взрослых).
        :return: Обновлённая модель пользователя или None, если пользователь не найден.
        """
        user_row: Optional[Record] = await self.db.fetchrow(
            """
            UPDATE users
            SET role = $2, monthly_income = $3
            WHERE id = $1
            RETURNING id, name, login, created_at, family_id, role, monthly_income
            """,
            (user_id, role, monthly_income),
        )

        if user_row is None:
            return None

        return User.model_validate(dict(user_row))

    async def get_family_members(self, family_id: int) -> List[User]:
        """
        Возвращает всех участников семьи.

        :param family_id: Идентификатор семьи.
        :return: Список пользователей, состоящих в этой семье.
        """
        rows = await self.db.fetch(
            """
            SELECT id, name, login, created_at, family_id, role, monthly_income
            FROM users
            WHERE family_id = $1
            ORDER BY created_at ASC
            """,
            (family_id,),
        )

        return [User.model_validate(dict(row)) for row in rows]


__all__ = [
    "UserRepository",
]