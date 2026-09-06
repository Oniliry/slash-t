from dependencies.expense import ExpenseServiceDep
from dependencies.family import CurrentUserDep
from fastapi import APIRouter

router = APIRouter(prefix="/debts", tags=["debts"])


@router.get("/me")
async def get_my_debts(
    user: CurrentUserDep,
    service: ExpenseServiceDep,
):
    """
    Возвращает долги текущего пользователя: те, что должен он сам,
    и те, что причитаются ему от других участников семьи.

    :param user: Текущий авторизованный пользователь.
    :param service: Сервис для работы с покупками и долгами.
    :return: Сводка долгов или сообщение об ошибке.
    """
    return await service.get_my_debts(user)


@router.post("/{debt_id}/confirm")
async def confirm_debt(
    debt_id: int,
    user: CurrentUserDep,
    service: ExpenseServiceDep,
):
    """
    Подтверждает погашение долга. Доступно только участнику, которому
    причитается перевод (получателю), — должник подтвердить сам за себя не может.

    :param debt_id: Идентификатор подтверждаемого долга.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис для работы с покупками и долгами.
    :return: Обновлённые данные долга или сообщение об ошибке.
    """
    return await service.confirm_debt(user, debt_id)


__all__ = [
    "router",
]
