from typing import Annotated

from fastapi import Depends

from database.base import db
from database.repositories.user_repo import UserRepository
from services.profile_service import ProfileService


def get_user_repo_for_profile() -> UserRepository:
    """
    Создаёт репозиторий пользователей для использования сервисом профиля.

    :return: Репозиторий пользователей с подключением к общей базе данных.
    """
    return UserRepository(db)


def get_profile_service(
    user_repo: UserRepository = Depends(get_user_repo_for_profile),
) -> ProfileService:
    """
    Создаёт сервис для изменения профиля пользователя.

    :param user_repo: Репозиторий пользователей, предоставленный FastAPI.
    :return: Сервис изменения имени, дохода и пароля.
    """
    return ProfileService(user_repo)


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]


__all__ = [
    "ProfileServiceDep",
]
