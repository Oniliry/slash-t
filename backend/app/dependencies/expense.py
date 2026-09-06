from typing import Annotated

from fastapi import Depends

from database.base import db
from database.repositories import DebtRepository, ExpenseRepository, FamilyRepository, UserRepository
from services.expense_service import ExpenseService


def get_expense_repo() -> ExpenseRepository:
    """
    Создаёт репозиторий покупок.

    :return: Репозиторий покупок с подключением к общей базе данных.
    """
    return ExpenseRepository(db)


def get_debt_repo() -> DebtRepository:
    """
    Создаёт репозиторий долгов.

    :return: Репозиторий долгов с подключением к общей базе данных.
    """
    return DebtRepository(db)


def get_family_repo_for_expense() -> FamilyRepository:
    """
    Создаёт репозиторий семей для использования сервисом покупок.

    :return: Репозиторий семей с подключением к общей базе данных.
    """
    return FamilyRepository(db)


def get_user_repo_for_expense() -> UserRepository:
    """
    Создаёт репозиторий пользователей для использования сервисом покупок.

    :return: Репозиторий пользователей с подключением к общей базе данных.
    """
    return UserRepository(db)


def get_expense_service(
    expense_repo: ExpenseRepository = Depends(get_expense_repo),
    debt_repo: DebtRepository = Depends(get_debt_repo),
    family_repo: FamilyRepository = Depends(get_family_repo_for_expense),
    user_repo: UserRepository = Depends(get_user_repo_for_expense),
) -> ExpenseService:
    """
    Создаёт сервис для добавления покупок и расчёта долгов.

    :param expense_repo: Репозиторий покупок, предоставленный FastAPI.
    :param debt_repo: Репозиторий долгов, предоставленный FastAPI.
    :param family_repo: Репозиторий семей, предоставленный FastAPI.
    :param user_repo: Репозиторий пользователей, предоставленный FastAPI.
    :return: Сервис добавления покупок и подтверждения долгов.
    """
    return ExpenseService(expense_repo, debt_repo, family_repo, user_repo)


ExpenseServiceDep = Annotated[ExpenseService, Depends(get_expense_service)]


__all__ = [
    "ExpenseServiceDep",
]
