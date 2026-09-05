from typing import Optional

from fastapi import APIRouter, Cookie, Response

from dependencies.auth import AuthServiceDep
from schemas.auth import UserLoginRequest, UserRegisterRequest


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register_user(
    data: UserRegisterRequest,
    service: AuthServiceDep,
    response: Response,
):
    """
    Регистрирует нового пользователя.

    :param data: Имя, логин и пароль нового пользователя.
    :param service: Сервис авторизации, предоставленный FastAPI.
    :return: Данные пользователя или сообщение о занятом логине.
    """
    return await service.register_user(data, response)


@router.post("/login")
async def login_user(
    data: UserLoginRequest,
    service: AuthServiceDep,
    response: Response,
):
    """
    Выполняет вход пользователя по логину и паролю.

    :param data: Логин и пароль пользователя.
    :param service: Сервис авторизации, предоставленный FastAPI.
    :return: Данные пользователя или ошибку с HTTP-кодом 401.
    """

    return await service.login_user(data, response)


@router.post("/me")
async def get_current_user(
    service: AuthServiceDep,
    access_token: Optional[str] = Cookie(default=None),
):
    """
    Возвращает текущего авторизованного пользователя.

    :param service: Сервис авторизации, предоставленный FastAPI.
    :param access_token: JWT-токен из HttpOnly cookie.
    :return: Данные текущего пользователя или ошибку авторизации.
    """
    return await service.get_current_user(access_token)


@router.post("/logout")
async def logout_user(
    service: AuthServiceDep,
    response: Response,
):
    """
    Завершает текущую сессию пользователя и удаляет JWT-cookie.

    :param service: Сервис авторизации, предоставленный FastAPI.
    :param response: HTTP-ответ для удаления access_token cookie.
    :return: Подтверждение выхода из аккаунта.
    """
    return service.logout_user(response)


__all__ = [
    "router",
]