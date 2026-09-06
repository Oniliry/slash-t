#backend/app/database/init_db.py

from database.base import db


async def create_tables():
    """
    Создаёт таблицы, необходимые для работы приложения.

    Таблица users хранит имя, логин, хэш пароля и дату регистрации.
    Таблица families хранит семейные пространства и код приглашения.
    Пользователь ссылается на свою семью и хранит роль (взрослый/ребёнок)
    и примерный месячный доход, если он взрослый.
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

    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS families (
            id SERIAL PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            invite_code VARCHAR(12) UNIQUE NOT NULL,
            created_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # Дополняем пользователя ссылкой на семью и данными о роли.
    # ADD COLUMN IF NOT EXISTS позволяет безопасно перезапускать инициализацию.
    await db.execute(
        """
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS family_id INTEGER REFERENCES families(id) ON DELETE SET NULL
        """
    )
    await db.execute(
        """
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS role VARCHAR(10) CHECK (role IN ('adult', 'child'))
        """
    )
    await db.execute(
        """
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS monthly_income NUMERIC(12, 2)
        """
    )

async def drop_tables():
    """
    Удаляет таблицы пользователей и семей.

    Метод предназначен для служебных сценариев и очистки тестовой базы.
    """
    await db.execute(
        """
        DROP TABLE IF EXISTS families CASCADE
        """
    )
    await db.execute(
        """
        DROP TABLE IF EXISTS users CASCADE
        """
    )

__all__ = [
    "create_tables",
    "drop_tables"
]