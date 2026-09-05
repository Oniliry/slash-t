from typing import Optional

from asyncpg import Record

from database.base import PostgresAsyncDatabase
from database.models.user import User


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
            RETURNING id, name, login, created_at
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
            SELECT id, name, login, password_hash, created_at
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
            SELECT id, name, login, created_at
            FROM users
            WHERE id = $1
            """,
            (user_id,),
        )

        if user_row is None:
            return None

        return User.model_validate(dict(user_row))


__all__ = [
    "UserRepository",
]