from dependencies.cushion import CushionServiceDep
from dependencies.family import CurrentUserDep
from fastapi import APIRouter

from schemas.cushion import CushionOperationRequest, SetCushionGoalRequest

router = APIRouter(prefix="/cushion", tags=["cushion"])


@router.get("")
async def get_cushion_state(
    user: CurrentUserDep,
    service: CushionServiceDep,
):
    """
    Возвращает состояние финансовой подушки семьи: текущий баланс,
    цель и прогресс накопления, ориентир средних расходов и историю
    операций — для страницы «ФинПодушка».

    :param user: Текущий авторизованный пользователь.
    :param service: Сервис финансовой подушки.
    :return: Состояние подушки или ошибку family_required.
    """
    return await service.get_state(user)


@router.post("/top-up")
async def top_up_cushion(
    data: CushionOperationRequest,
    user: CurrentUserDep,
    service: CushionServiceDep,
):
    """
    Пополняет финансовую подушку семьи.

    :param data: Сумма и комментарий.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис финансовой подушки.
    :return: Обновлённое состояние подушки или ошибку family_required.
    """
    return await service.top_up(user, data)


@router.post("/withdraw")
async def withdraw_cushion(
    data: CushionOperationRequest,
    user: CurrentUserDep,
    service: CushionServiceDep,
):
    """
    Списывает средства из финансовой подушки семьи.

    :param data: Сумма и комментарий.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис финансовой подушки.
    :return: Обновлённое состояние подушки, ошибку family_required
        или ошибку недостаточно средств.
    """
    return await service.withdraw(user, data)


@router.post("/goal")
async def set_cushion_goal(
    data: SetCushionGoalRequest,
    user: CurrentUserDep,
    service: CushionServiceDep,
):
    """
    Устанавливает или обновляет цель по финансовой подушке семьи.

    :param data: Целевая сумма и число месяцев.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис финансовой подушки.
    :return: Обновлённое состояние подушки или ошибку family_required.
    """
    return await service.set_goal(user, data)


__all__ = [
    "router",
]
