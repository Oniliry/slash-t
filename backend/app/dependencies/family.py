from typing import Annotated, Optional

from fastapi import Depends, HTTPException

from database.base import db
from database.models.user import User
from database.repositories import FamilyRepository, UserRepository
from dependencies.token import get_bearer_token
from services.auth_service import AuthService
from services.family_service import FamilyService


def get_family_repo() -> FamilyRepository:
    """
    Создаёт репозиторий семей.

    :return: Репозиторий семей с подключением к общей базе данных.
    """
    return FamilyRepository(db)


def get_user_repo_for_family() -> UserRepository:
    """
    Создаёт репозиторий пользователей для использования сервисом семьи.

    :return: Репозиторий пользователей с подключением к общей базе данных.
    """
    return UserRepository(db)


def get_family_service(
    family_repo: FamilyRepository = Depends(get_family_repo),
    user_repo: UserRepository = Depends(get_user_repo_for_family),
) -> FamilyService:
    """
    Создаёт сервис для работы с семьями и ролями участников.

    :param family_repo: Репозиторий семей, предоставленный FastAPI.
    :param user_repo: Репозиторий пользователей, предоставленный FastAPI.
    :return: Сервис создания/входа в семью и выбора роли.
    """
    return FamilyService(family_repo, user_repo)


async def get_current_active_user(
    access_token: Optional[str] = Depends(get_bearer_token),
    user_repo: UserRepository = Depends(get_user_repo_for_family),
) -> User:
    """
    Достаёт текущего авторизованного пользователя из JWT в заголовке Authorization.

    Используется роутером семьи, которому для операций (создание семьи,
    выбор роли и т.д.) нужен не просто факт авторизации, а сам объект User.

    :param access_token: JWT-токен из заголовка Authorization: Bearer.
    :param user_repo: Репозиторий пользователей, предоставленный FastAPI.
    :return: Текущий авторизованный пользователь.
    :raises HTTPException: 401, если пользователь не авторизован.
    """
    if not access_token:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован.")

    user_id = AuthService.get_user_id_from_token(access_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Недействительный или просроченный токен.")

    user = await user_repo.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден.")

    return user


FamilyServiceDep = Annotated[FamilyService, Depends(get_family_service)]
CurrentUserDep = Annotated[User, Depends(get_current_active_user)]


__all__ = [
    "FamilyServiceDep",
    "CurrentUserDep",
]
