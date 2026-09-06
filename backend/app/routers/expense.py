from dependencies.expense import ExpenseServiceDep
from dependencies.family import CurrentUserDep
from fastapi import APIRouter

from schemas.expense import CreateExpenseRequest

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("")
async def create_expense(
    data: CreateExpenseRequest,
    user: CurrentUserDep,
    service: ExpenseServiceDep,
):
    """
    Добавляет покупку. В зависимости от того, кому она принадлежит
    (себе / участнику семьи / общая), автоматически создаёт долги перед
    заплатившим пользователем.

    :param data: Сумма покупки, категория и кому она принадлежит.
    :param user: Текущий авторизованный пользователь (плательщик).
    :param service: Сервис для работы с покупками и долгами.
    :return: Данные покупки вместе со списком созданных долгов или ошибку.
    """
    return await service.create_expense(user, data)


@router.get("")
async def list_expenses(
    user: CurrentUserDep,
    service: ExpenseServiceDep,
    limit: int = 50,
):
    """
    Возвращает историю последних покупок семьи — для вкладки «Расходы».

    :param user: Текущий авторизованный пользователь.
    :param service: Сервис для работы с покупками и долгами.
    :param limit: Максимальное количество покупок в ответе.
    :return: Список покупок, отсортированный от новых к старым, или ошибку.
    """
    return await service.list_expenses(user, limit=limit)


__all__ = [
    "router",
]
