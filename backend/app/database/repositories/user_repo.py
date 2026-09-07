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

    async def update_name(self, user_id: int, name: str) -> Optional[User]:
        """
        Обновляет отображаемое имя пользователя (видно другим членам семьи).

        :param user_id: Уникальный идентификатор пользователя.
        :param name: Новое имя пользователя.
        :return: Обновлённая модель пользователя или None, если пользователь не найден.
        """
        user_row: Optional[Record] = await self.db.fetchrow(
            """
            UPDATE users
            SET name = $2
            WHERE id = $1
            RETURNING id, name, login, created_at, family_id, role, monthly_income
            """,
            (user_id, name),
        )

        if user_row is None:
            return None

        return User.model_validate(dict(user_row))

    async def update_monthly_income(
        self,
        user_id: int,
        monthly_income: Decimal,
    ) -> Optional[User]:
        """
        Обновляет примерный месячный доход пользователя (только для взрослых).

        Роль не меняется, меняется только сумма дохода — от неё зависит
        автоматически пересчитываемая доля участника в общем бюджете семьи.

        :param user_id: Уникальный идентификатор пользователя.
        :param monthly_income: Новый примерный месячный доход.
        :return: Обновлённая модель пользователя или None, если пользователь не найден.
        """
        user_row: Optional[Record] = await self.db.fetchrow(
            """
            UPDATE users
            SET monthly_income = $2
            WHERE id = $1
            RETURNING id, name, login, created_at, family_id, role, monthly_income
            """,
            (user_id, monthly_income),
        )

        if user_row is None:
            return None

        return User.model_validate(dict(user_row))

    async def get_password_hash(self, user_id: int) -> Optional[str]:
        """
        Возвращает хэш пароля пользователя для проверки текущего пароля.

        :param user_id: Уникальный идентификатор пользователя.
        :return: Хэш пароля или None, если пользователь не найден.
        """
        value = await self.db.fetchval(
            """
            SELECT password_hash
            FROM users
            WHERE id = $1
            """,
            (user_id,),
        )
        return value

    async def update_password(self, user_id: int, password_hash: str) -> bool:
        """
        Обновляет хэш пароля пользователя.

        :param user_id: Уникальный идентификатор пользователя.
        :param password_hash: Новый хэш пароля.
        :return: True, если пароль был обновлён.
        """
        user_row: Optional[Record] = await self.db.fetchrow(
            """
            UPDATE users
            SET password_hash = $2
            WHERE id = $1
            RETURNING id
            """,
            (user_id, password_hash),
        )
        return user_row is not None

    async def update_member_fields(
        self,
        user_id: int,
        name: Optional[str],
        monthly_income: Optional[Decimal],
        set_income: bool,
    ) -> Optional[User]:
        """
        Обновляет имя и/или доход участника семьи (используется админом).

        :param user_id: Уникальный идентификатор пользователя.
        :param name: Новое имя, если его нужно изменить.
        :param monthly_income: Новый доход, если его нужно изменить.
        :param set_income: True, если доход нужно обновить (даже если None).
        :return: Обновлённая модель пользователя или None, если пользователь не найден.
        """
        if name is not None and set_income:
            user_row: Optional[Record] = await self.db.fetchrow(
                """
                UPDATE users
                SET name = $2, monthly_income = $3
                WHERE id = $1
                RETURNING id, name, login, created_at, family_id, role, monthly_income
                """,
                (user_id, name, monthly_income),
            )
        elif name is not None:
            user_row = await self.db.fetchrow(
                """
                UPDATE users
                SET name = $2
                WHERE id = $1
                RETURNING id, name, login, created_at, family_id, role, monthly_income
                """,
                (user_id, name),
            )
        elif set_income:
            user_row = await self.db.fetchrow(
                """
                UPDATE users
                SET monthly_income = $2
                WHERE id = $1
                RETURNING id, name, login, created_at, family_id, role, monthly_income
                """,
                (user_id, monthly_income),
            )
        else:
            return await self.get_user(user_id)

        if user_row is None:
            return None

        return User.model_validate(dict(user_row))

    async def clear_user_family(self, user_id: int) -> Optional[User]:
        """
        Убирает пользователя из семьи (используется при удалении участника админом).

        Сбрасывает семью, роль и доход — пользователю нужно будет заново
        пройти шаги "семья" и "роль" при следующем входе.

        :param user_id: Уникальный идентификатор пользователя.
        :return: Обновлённая модель пользователя или None, если пользователь не найден.
        """
        user_row: Optional[Record] = await self.db.fetchrow(
            """
            UPDATE users
            SET family_id = NULL, role = NULL, monthly_income = NULL
            WHERE id = $1
            RETURNING id, name, login, created_at, family_id, role, monthly_income
            """,
            (user_id,),
        )

        if user_row is None:
            return None

        return User.model_validate(dict(user_row))


__all__ = [
    "UserRepository",
]