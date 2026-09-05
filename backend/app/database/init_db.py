#backend/app/database/init_db.py

from database.base import db


async def create_tables():
    """
    Создаёт таблицы, необходимые для работы приложения.

    Таблица users хранит имя, логин, хэш пароля и дату регистрации.
    """
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            login VARCHAR(50) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

async def drop_tables():
    """
    Удаляет таблицу пользователей.

    Метод предназначен для служебных сценариев и очистки тестовой базы.
    """
    await db.execute(
        """
        DROP TABLE IF EXISTS users
        """
    )

__all__ = [
    "create_tables",
    "drop_tables"
]