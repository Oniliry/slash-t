#backend/app/database/base.py

import asyncpg

from typing import Any, List, Optional, Tuple

from asyncpg.pool import Pool
from asyncpg import Record
from redis import Redis

from logger import logger

from core.config import DATABASE_URL

class PostgresAsyncDatabase:
    """
    Базовый класс для работы с PostgreSQL.
    """
    def __init__(self, database_url: str, min_size: int = 1, max_size: int = 10) -> None:
        """
        Инициализация базы данных.

        :param database_url: URL для подключения к PostgreSQL.
        :param min_size: Минимальное количество соединений в пуле.
        :param max_size: Максимальное количество соединений в пуле.
        """
        self.database_url: str = database_url
        self.min_size: int = min_size
        self.max_size: int = max_size
        
        self.pool: Optional[Pool] = None

    async def connect(self) -> None:
        """
        Создает пул соединений с базой.
        """
        if self.pool is None:
            self.pool: Pool = await asyncpg.create_pool(
                dsn=self.database_url,
                min_size=self.min_size,
                max_size=self.max_size
            )

    async def close(self) -> None:
        """
        Закрывает пул соединений с базой.
        """
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def execute(self, query: str, params: Tuple[Any, ...] = ()) -> None:
        """
        Выполняет запрос на изменение данных.

        :param query: SQL-запрос.
        :param params: Значения для плейсхолдеров.
        """
        if self.pool is None:
            raise RuntimeError("Пул не инициализирован.")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                try:
                    await conn.execute(query, *params)
                except Exception as e:
                    raise RuntimeError(f"Ошибка выполнения запроса на изменение: {e}")

    async def fetch(self, query: str, params: Tuple[Any, ...] = ()) -> List[Record]:
        """
        Выполняет SELECT-запрос и возвращает список записей.

        :param query: SQL-запрос.
        :param params: Значения для плейсхолдеров.
        :return: Список значений.
        """
        if self.pool is None:
            raise RuntimeError("Пул не инициализирован.")

        async with self.pool.acquire() as conn:
            try:
                return await conn.fetch(query, *params)
            except Exception as e:
                raise RuntimeError(f"Ошибка выполнения запроса на чтение: {e}")

    async def fetchrow(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[Record]:
        """
        Выполняет SELECT-запрос и возвращает одну запись.

        :param query: SQL-запрос.
        :param params: Значения для плейсхолдеров.
        :return: Одну запись.
        """
        if self.pool is None:
            raise RuntimeError("Пул не инициализирован.")

        async with self.pool.acquire() as conn:
            try:
                return await conn.fetchrow(query, *params)
            except Exception as e:
                raise RuntimeError(f"Ошибка выполнения запроса на чтение: {e}")

    async def fetchval(self, query: str, params: Tuple[Any, ...] = ()) -> Any:
        """
        Выполняет SELECT-запрос и возвращает одно значение.

        :param query: SQL-запрос.
        :param params: Значения для плейсхолдеров.
        :return: Одно значение.
        """
        if self.pool is None:
            raise RuntimeError("Пул не инициализирован.")
        
        async with self.pool.acquire() as conn:
            try:
                return await conn.fetchval(query, *params)
            except Exception as e:
                raise RuntimeError(f"Ошибка выполнения запроса на чтение значения: {e}")

db = PostgresAsyncDatabase(DATABASE_URL)

r = None

# try:
#     r = Redis(
#         host="localhost",
#         port=6379,
#         db=0,
#         decode_responses=True
#     )
# except Exception as e:
#     logger.error(f"Ошибка подключения к Redis: {e}")

# r.flushdb()

__all__ = [
    "PostgresAsyncDatabase",
    "db",
    "r"
]