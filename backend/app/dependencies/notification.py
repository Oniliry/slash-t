from typing import Annotated

from fastapi import Depends

from database.base import db
from database.repositories import DebtRepository, ExpenseRepository, UserRepository
from services.notification_service import NotificationService


def get_debt_repo() -> DebtRepository:
    return DebtRepository(db)


def get_expense_repo() -> ExpenseRepository:
    return ExpenseRepository(db)


def get_user_repo() -> UserRepository:
    return UserRepository(db)


def get_notification_service(
    debt_repo: DebtRepository = Depends(get_debt_repo),
    expense_repo: ExpenseRepository = Depends(get_expense_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> NotificationService:
    return NotificationService(debt_repo, expense_repo, user_repo)


NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]

__all__ = [
    "NotificationServiceDep",
    "get_notification_service",
]
