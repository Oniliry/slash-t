import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Response

from core.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET
from database.repositories.user_repo import UserRepository
from schemas.auth import UserLoginRequest, UserRegisterRequest, UserResponse
from schemas.base import APIResponse


class AuthService:
    """Сервис регистрации и входа пользователей."""

    def __init__(self, repo: UserRepository):
        """
        Инициализация сервиса авторизации.

        :param repo: Репозиторий для работы с пользователями.
        """
        self.repo = repo

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Создаёт безопасный хэш пароля с уникальной солью.

        :param password: Открытый пароль пользователя.
        :return: Строка с алгоритмом, солью и хэшем пароля.
        """
        salt = secrets.token_bytes(16)
        password_hash = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=2**14,
            r=8,
            p=1,
        )
        return f"scrypt${salt.hex()}${password_hash.hex()}"

    @staticmethod
    def verify_password(password: str, encoded_password: str) -> bool:
        """
        Проверяет пароль по сохранённому хэшу.

        :param password: Пароль, введённый пользователем.
        :param encoded_password: Сохранённая строка с хэшем пароля.
        :return: True, если пароль совпадает, иначе False.
        """
        try:
            algorithm, salt_hex, hash_hex = encoded_password.split("$", 2)
            if algorithm != "scrypt":
                return False

            password_hash = hashlib.scrypt(
                password.encode("utf-8"),
                salt=bytes.fromhex(salt_hex),
                n=2**14,
                r=8,
                p=1,
            )
            return hmac.compare_digest(password_hash.hex(), hash_hex)
        except (ValueError, TypeError):
            return False

    @staticmethod
    def create_access_token(user_id: int) -> str:
        """
        Создаёт JWT-токен для пользователя.

        :param user_id: Уникальный идентификатор пользователя.
        :return: Подписанный JWT-токен.
        """
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=JWT_EXPIRE_MINUTES),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def set_auth_cookie(response: Response, token: str) -> None:
        """
        Сохраняет JWT-токен в HttpOnly cookie.

        :param response: HTTP-ответ FastAPI.
        :param token: JWT-токен авторизации.
        """
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=JWT_EXPIRE_MINUTES * 60,
        )

    @staticmethod
    def delete_auth_cookie(response: Response) -> None:
        """
        Удаляет JWT-токен авторизации из cookie.

        :param response: HTTP-ответ FastAPI.
        """
        response.delete_cookie(
            key="access_token",
            httponly=True,
            secure=False,
            samesite="lax",
            path="/",
        )

    def logout_user(self, response: Response) -> APIResponse[None]:
        """
        Завершает авторизацию пользователя.

        :param response: HTTP-ответ, из которого будет удалена cookie.
        :return: Подтверждение завершения сессии.
        """
        self.delete_auth_cookie(response)

        return APIResponse.success(message="Выход выполнен успешно.")

    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[int]:
        """
        Извлекает идентификатор пользователя из JWT-токена.

        :param token: JWT-токен из cookie.
        :return: Идентификатор пользователя или None для недействительного токена.
        """
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
            )
            user_id = payload.get("sub")
            return int(user_id) if user_id is not None else None
        except (jwt.InvalidTokenError, TypeError, ValueError):
            return None

    async def register_user(
        self,
        data: UserRegisterRequest,
        response: Response,
    ) -> APIResponse[UserResponse]:
        """
        Регистрирует пользователя в системе.

        :param data: Данные для регистрации пользователя.
        :param response: HTTP-ответ, в который будет установлена cookie авторизации.
        :return: Публичные данные созданного пользователя или сообщение об ошибке.
        """
        existing_user = await self.repo.get_user_by_login(data.login)
        if existing_user is not None:
            return APIResponse.warn(
                message="Пользователь с таким логином уже зарегистрирован.",
                type="login_already_exists",
            )

        user = await self.repo.add_user(
            name=data.name,
            login=data.login,
            password_hash=self.hash_password(data.password),
        )
        self.set_auth_cookie(response, self.create_access_token(user.id))

        return APIResponse.success(
            data=UserResponse.model_validate(user),
            message="Пользователь успешно зарегистрирован.",
        )

    async def login_user(
        self,
        data: UserLoginRequest,
        response: Response,
    ) -> APIResponse[UserResponse]:
        """
        Проверяет логин и пароль пользователя.

        :param data: Данные для входа пользователя.
        :param response: HTTP-ответ, в который будет установлена cookie авторизации.
        :return: Публичные данные пользователя или ошибку авторизации.
        """
        user_row = await self.repo.get_user_by_login(data.login)
        if user_row is None or not self.verify_password(
            data.password,
            user_row["password_hash"],
        ):
            return APIResponse.fail(
                message="Неверный логин или пароль.",
                status_code=401,
                type="invalid_credentials",
            )

        self.set_auth_cookie(response, self.create_access_token(int(user_row["id"])))

        return APIResponse.success(
            data=UserResponse.model_validate(dict(user_row)),
            message="Вход выполнен успешно.",
        )

    async def get_current_user(self, token: Optional[str]) -> APIResponse[UserResponse]:
        """
        Возвращает текущего пользователя по JWT из cookie.

        :param token: JWT-токен из cookie access_token.
        :return: Данные текущего пользователя или ошибку авторизации.
        """
        if not token:
            return APIResponse.fail(
                message="Пользователь не авторизован.",
                status_code=401,
                type="authentication_required",
            )

        user_id = self.get_user_id_from_token(token)
        if user_id is None:
            return APIResponse.fail(
                message="Недействительный или просроченный токен.",
                status_code=401,
                type="invalid_token",
            )

        user = await self.repo.get_user(user_id)
        if user is None:
            return APIResponse.fail(
                message="Пользователь не найден.",
                status_code=401,
                type="user_not_found",
            )

        return APIResponse.success(
            data=UserResponse.model_validate(user),
            message="Текущий пользователь успешно получен.",
        )


__all__ = [
    "AuthService",
]