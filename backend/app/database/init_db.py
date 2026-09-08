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

    # Название покупки (например, магазин с чека) — опционально, для чеков.
    await db.execute(
        """
        ALTER TABLE expenses
            ADD COLUMN IF NOT EXISTS shop_name VARCHAR(150)
        """
    )

    # Позиции покупки, если она добавлена через распознавание чека —
    # одна покупка (expense) хранит несколько товаров.
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS expense_items (
            id SERIAL PRIMARY KEY,
            expense_id INTEGER NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
            name VARCHAR(200) NOT NULL,
            sum NUMERIC(12, 2) NOT NULL CHECK (sum > 0),
            category VARCHAR(20) NOT NULL DEFAULT 'other',
            position INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    # Владелец конкретного товара внутри чека (личное/общее у каждой позиции
    # может отличаться от других позиций того же чека).
    await db.execute(
        """
        ALTER TABLE expense_items
            ADD COLUMN IF NOT EXISTS owner_type VARCHAR(10) NOT NULL DEFAULT 'shared'
            CHECK (owner_type IN ('self', 'member', 'shared'))
        """
    )
    await db.execute(
        """
        ALTER TABLE expense_items
            ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL
        """
    )

    # Финподушка: ручной баланс/цель и история операций (пополнение/списание).
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS cushion_operations (
            id SERIAL PRIMARY KEY,
            family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            op_type VARCHAR(10) NOT NULL CHECK (op_type IN ('top-up', 'withdraw')),
            amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
            comment VARCHAR(200) NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS cushion_goals (
            family_id INTEGER PRIMARY KEY REFERENCES families(id) ON DELETE CASCADE,
            target_amount NUMERIC(14, 2) NOT NULL CHECK (target_amount >= 0),
            months INTEGER NOT NULL DEFAULT 6,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # Последний анализ PDF-выписки каждого участника семьи:
    # ключ — user_id (у каждого своя выписка), payload — полный JSON
    # результата analyze_statement, cushion_total денормализован для рейтинга.
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
    Удаляет таблицы пользователей, семей, покупок и долгов.

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
        DROP TABLE IF EXISTS expense_items CASCADE
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