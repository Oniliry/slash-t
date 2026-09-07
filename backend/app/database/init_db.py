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

    # Таблица expenses хранит покупки, добавленные участниками семьи:
    # кто заплатил, сколько и кому принадлежит покупка (себе/участнику/общая).
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
            payer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
            owner_type VARCHAR(10) NOT NULL CHECK (owner_type IN ('self', 'member', 'shared')),
            owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # Категория покупки (продукты, ЖКХ, транспорт и т.д.) — по умолчанию
    # "other", пользователь может скорректировать её вручную.
    await db.execute(
        """
        ALTER TABLE expenses
            ADD COLUMN IF NOT EXISTS category VARCHAR(20) NOT NULL DEFAULT 'other'
            CHECK (category IN (
                'groceries', 'utilities', 'transport', 'cafe',
                'entertainment', 'health', 'clothing', 'other'
            ))
        """
    )

    # Таблица debts хранит взаиморасчёты, порождённые покупками: кто кому
    # и сколько должен, и подтверждено ли погашение получателем перевода.
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS debts (
            id SERIAL PRIMARY KEY,
            expense_id INTEGER NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
            family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
            debtor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            creditor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
            status VARCHAR(10) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            confirmed_at TIMESTAMPTZ
        )
        """
    )

    # Статус "netted" добавлен позже — расширяем ограничение на уже
    # существующих базах (ADD CONSTRAINT с IF NOT EXISTS через DROP+ADD,
    # чтобы миграцию можно было безопасно перезапускать).
    await db.execute(
        """
        ALTER TABLE debts DROP CONSTRAINT IF EXISTS debts_status_check
        """
    )
    await db.execute(
        """
        ALTER TABLE debts
            ADD CONSTRAINT debts_status_check CHECK (status IN ('pending', 'confirmed', 'netted'))
        """
    )

    # Таблица cushion_operations хранит историю пополнений и списаний
    # финансовой подушки семьи: сколько отложили, сколько потратили
    # из резерва и на что.
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS cushion_operations (
            id SERIAL PRIMARY KEY,
            family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            kind VARCHAR(10) NOT NULL CHECK (kind IN ('topup', 'withdraw')),
            amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
            comment VARCHAR(200),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # Таблица cushion_goals хранит цель накоплений семьи: целевая сумма
    # и на сколько месяцев расходов она рассчитана (цель одна на семью).
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS cushion_goals (
            family_id INTEGER PRIMARY KEY REFERENCES families(id) ON DELETE CASCADE,
            target_amount NUMERIC(14, 2) NOT NULL CHECK (target_amount > 0),
            months INTEGER NOT NULL DEFAULT 6 CHECK (months BETWEEN 1 AND 60),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # Таблица cushion_analysis хранит последний анализ PDF-выписки
    # каждого участника семьи: у каждого члена семьи своя выписка,
    # поэтому ключ — user_id. payload содержит полный JSON результата
    # analyze_statement (месяцы, транзакции, кандидаты-переводы),
    # cushion_total денормализован для рейтинга семьи.
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS cushion_analysis (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
            months_analyzed INTEGER NOT NULL DEFAULT 0,
            cushion_total NUMERIC(14, 2) NOT NULL DEFAULT 0,
            full_months JSONB NOT NULL DEFAULT '[]',
            excluded_months JSONB NOT NULL DEFAULT '[]',
            payload JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

async def drop_tables():
    """
    Удаляет таблицы пользователей, семей, покупок, долгов и подушки.

    Метод предназначен для служебных сценариев и очистки тестовой базы.
    """
    await db.execute(
        """
        DROP TABLE IF EXISTS cushion_analysis CASCADE
        """
    )
    await db.execute(
        """
        DROP TABLE IF EXISTS cushion_goals CASCADE
        """
    )
    await db.execute(
        """
        DROP TABLE IF EXISTS cushion_operations CASCADE
        """
    )
    await db.execute(
        """
        DROP TABLE IF EXISTS debts CASCADE
        """
    )
    await db.execute(
        """
        DROP TABLE IF EXISTS expenses CASCADE
        """
    )
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