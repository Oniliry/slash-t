from typing import Optional

from fastapi import Cookie, Header

from core.config import JWT_COOKIE_NAME


def get_bearer_token(
    authorization: Optional[str] = Header(default=None),
    access_token: Optional[str] = Cookie(default=None, alias=JWT_COOKIE_NAME),
) -> Optional[str]:
    """
    Достаёт JWT-токен из Bearer-заголовка или HttpOnly cookie.

    Токен специально передаётся заголовком, а не cookie: cookie общая на весь
    браузер (все вкладки одного домена делят одну и ту же сессию), из-за чего
    вход в аккаунт в одной вкладке сбрасывал сессию в другой. Фронтенд хранит
    токен в sessionStorage, который у каждой вкладки свой, — так сессии вкладок
    не пересекаются.

    :param authorization: Значение заголовка Authorization, предоставленное FastAPI.
    :param access_token: JWT из HttpOnly cookie.
    :return: Токен без префикса "Bearer", либо None, если заголовка нет или он некорректен.
    """
    if not authorization:
        return access_token

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return access_token

    return token


__all__ = [
    "get_bearer_token",
]
