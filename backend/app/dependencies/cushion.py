from typing import Annotated

from fastapi import Depends

from database.base import db
from database.repositories import CushionRepository, ExpenseRepository, UserRepository
from services.cushion_service import CushionService


def get_cushion_repo() -> CushionRepository:
    """
    Создаёт репозиторий финансовой подушки.

    :return: Репозиторий операций и цели подушки с общим подключением к БД.
    """
    return CushionRepository(db)


def get_expense_repo_for_cushion() -> ExpenseRepository:
    """
    Создаёт репозиторий покупок для расчёта ориентира расходов.

    :return: Репозиторий покупок с подключением к общей базе данных.
    """
    return ExpenseRepository(db)


def get_user_repo_for_cushion() -> UserRepository:
    """
    Создаёт репозиторий пользователей для имён в истории операций.

    :return: Репозиторий пользователей с подключением к общей базе данных.
    """
    return UserRepository(db)


def get_cushion_service(
    cushion_repo: CushionRepository = Depends(get_cushion_repo),
    expense_repo: ExpenseRepository = Depends(get_expense_repo_for_cushion),
    user_repo: UserRepository = Depends(get_user_repo_for_cushion),
) -> CushionService:
    """
    Создаёт сервис финансовой подушки.

    :param cushion_repo: Репозиторий подушки, предоставленный FastAPI.
    :param expense_repo: Репозиторий покупок, предоставленный FastAPI.
    :param user_repo: Репозиторий пользователей, предоставленный FastAPI.
    :return: Сервис подушки: баланс, цель, пополнение и списание.
    """
    return CushionService(cushion_repo, expense_repo, user_repo)


CushionServiceDep = Annotated[CushionService, Depends(get_cushion_service)]


__all__ = [
    "CushionServiceDep",
]
