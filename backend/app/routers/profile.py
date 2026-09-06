from dependencies.family import CurrentUserDep
from dependencies.profile import ProfileServiceDep
from fastapi import APIRouter
from schemas.profile import ChangePasswordRequest, UpdateIncomeRequest, UpdateNameRequest

router = APIRouter(prefix="/profile", tags=["profile"])


@router.patch("/name")
async def update_name(
    data: UpdateNameRequest,
    user: CurrentUserDep,
    service: ProfileServiceDep,
):
    """
    Меняет отображаемое имя текущего пользователя.

    :param data: Новое имя.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис изменения профиля.
    :return: Обновлённые данные пользователя.
    """
    return await service.update_name(user, data)


@router.patch("/income")
async def update_income(
    data: UpdateIncomeRequest,
    user: CurrentUserDep,
    service: ProfileServiceDep,
):
    """
    Меняет примерный месячный доход текущего пользователя (только для взрослых).

    :param data: Новый месячный доход.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис изменения профиля.
    :return: Обновлённые данные пользователя или сообщение об ошибке.
    """
    return await service.update_income(user, data)


@router.patch("/password")
async def change_password(
    data: ChangePasswordRequest,
    user: CurrentUserDep,
    service: ProfileServiceDep,
):
    """
    Меняет пароль текущего пользователя после проверки текущего пароля.

    :param data: Текущий и новый пароль.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис изменения профиля.
    :return: Подтверждение смены пароля или сообщение об ошибке.
    """
    return await service.change_password(user, data)


__all__ = [
    "router",
]
