from typing import Annotated

from fastapi import Depends

from database.base import db
from database.repositories import UserRepository
from services.auth_service import AuthService


def get_user_repo() -> UserRepository:
    """
    Создаёт репозиторий пользователей.

    :return: Репозиторий пользователей с подключением к общей базе данных.
    """

    return UserRepository(db)


def get_auth_service(
    repo: UserRepository = Depends(get_user_repo),
) -> AuthService:
    """
    Создаёт сервис авторизации.

    :param repo: Репозиторий пользователей, предоставленный FastAPI.
    :return: Сервис регистрации и входа пользователей.
    """

    return AuthService(repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


__all__ = [
    "AuthServiceDep",
]