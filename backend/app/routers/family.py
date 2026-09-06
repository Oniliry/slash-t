from dependencies.family import CurrentUserDep, FamilyServiceDep
from fastapi import APIRouter
from schemas.family import CreateFamilyRequest, JoinFamilyRequest, SetRoleRequest

router = APIRouter(prefix="/family", tags=["family"])


@router.post("/create")
async def create_family(
    data: CreateFamilyRequest,
    user: CurrentUserDep,
    service: FamilyServiceDep,
):
    """
    Создаёт новую семью и делает текущего пользователя её создателем.

    :param data: Название новой семьи.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис для работы с семьями.
    :return: Данные семьи вместе с кодом приглашения или сообщение об ошибке.
    """
    return await service.create_family(user, data)


@router.post("/join")
async def join_family(
    data: JoinFamilyRequest,
    user: CurrentUserDep,
    service: FamilyServiceDep,
):
    """
    Присоединяет текущего пользователя к существующей семье по коду приглашения.

    :param data: Код приглашения семьи.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис для работы с семьями.
    :return: Данные семьи, к которой присоединился пользователь, или ошибку.
    """
    return await service.join_family(user, data)


@router.post("/role")
async def set_role(
    data: SetRoleRequest,
    user: CurrentUserDep,
    service: FamilyServiceDep,
):
    """
    Сохраняет роль пользователя в семье (взрослый/ребёнок) и его доход.

    :param data: Роль и, для взрослых, примерный месячный доход.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис для работы с семьями.
    :return: Данные участника семьи с сохранённой ролью или сообщение об ошибке.
    """
    return await service.set_role(user, data)


@router.get("/me")
async def get_my_family(
    user: CurrentUserDep,
    service: FamilyServiceDep,
):
    """
    Возвращает данные семьи текущего пользователя и список участников с долями бюджета.

    :param user: Текущий авторизованный пользователь.
    :param service: Сервис для работы с семьями.
    :return: Полное состояние семьи или сообщение о том, что семьи ещё нет.
    """
    return await service.get_my_family(user)


__all__ = [
    "router",
]
