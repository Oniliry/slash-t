from dependencies.family import CurrentUserDep, FamilyServiceDep
from fastapi import APIRouter
from schemas.family import (
    BudgetSplitRequest,
    CreateFamilyRequest,
    JoinFamilyRequest,
    RenameFamilyRequest,
    SetRoleRequest,
    UpdateMemberRequest,
)

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


@router.patch("/name")
async def rename_family(
    data: RenameFamilyRequest,
    user: CurrentUserDep,
    service: FamilyServiceDep,
):
    """
    Переименовывает семью. Доступно только админу (создателю семьи).

    :param data: Новое название семьи.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис для работы с семьями.
    :return: Обновлённые данные семьи или сообщение об ошибке.
    """
    return await service.rename_family(user, data)


@router.patch("/members/{member_id}")
async def update_member(
    member_id: int,
    data: UpdateMemberRequest,
    user: CurrentUserDep,
    service: FamilyServiceDep,
):
    """
    Обновляет имя и/или доход участника семьи. Доступно только админу.

    :param member_id: Идентификатор редактируемого участника.
    :param data: Новое имя и/или доход участника.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис для работы с семьями.
    :return: Обновлённое состояние семьи или сообщение об ошибке.
    """
    return await service.update_member(user, member_id, data)


@router.delete("/members/{member_id}")
async def remove_member(
    member_id: int,
    user: CurrentUserDep,
    service: FamilyServiceDep,
):
    """
    Удаляет участника из семьи. Доступно только админу.

    :param member_id: Идентификатор удаляемого участника.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис для работы с семьями.
    :return: Обновлённое состояние семьи или сообщение об ошибке.
    """
    return await service.remove_member(user, member_id)


@router.patch("/budget-split")
async def update_budget_split(
    data: BudgetSplitRequest,
    user: CurrentUserDep,
    service: FamilyServiceDep,
):
    """
    Перераспределяет доход между двумя соседними взрослыми участниками
    (перетаскивание точки на полоске общего бюджета). Доступно только админу.

    :param data: Пара участников и новая доля первого из них в сумме доходов пары.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис для работы с семьями.
    :return: Обновлённое состояние семьи или сообщение об ошибке.
    """
    return await service.update_budget_split(user, data)


__all__ = [
    "router",
]
