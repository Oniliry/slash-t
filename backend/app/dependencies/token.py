from typing import Optional

from fastapi import Header


def get_bearer_token(authorization: Optional[str] = Header(default=None)) -> Optional[str]:
    """
    Достаёт JWT-токен из заголовка `Authorization: Bearer <token>`.

    Токен специально передаётся заголовком, а не cookie: cookie общая на весь
    браузер (все вкладки одного домена делят одну и ту же сессию), из-за чего
    вход в аккаунт в одной вкладке сбрасывал сессию в другой. Фронтенд хранит
    токен в sessionStorage, который у каждой вкладки свой, — так сессии вкладок
    не пересекаются.

    :param authorization: Значение заголовка Authorization, предоставленное FastAPI.
    :return: Токен без префикса "Bearer", либо None, если заголовка нет или он некорректен.
    """
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    return token


__all__ = [
    "get_bearer_token",
]
