import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from core.config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET
from database.repositories.user_repo import UserRepository
from schemas.auth import AuthResponse, UserLoginRequest, UserRegisterRequest, UserResponse
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

    def logout_user(self) -> APIResponse[None]:
        """
        Завершает авторизацию пользователя.

        Токен — стейтлес JWT без серверного хранения сессий, поэтому на
        бэкенде отзывать нечего: фронтенд просто удаляет токен из
        sessionStorage своей вкладки.

        :return: Подтверждение завершения сессии.
        """
        return APIResponse.success(message="Выход выполнен успешно.")

    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[int]:
        """
        Извлекает идентификатор пользователя из JWT-токена.

        :param token: JWT-токен из заголовка Authorization: Bearer.
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
    ) -> APIResponse[AuthResponse]:
        """
        Регистрирует пользователя в системе.

        :param data: Данные для регистрации пользователя.
        :return: Данные пользователя вместе с токеном сессии или сообщение об ошибке.
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

        return APIResponse.success(
            data=AuthResponse(
                user=UserResponse.model_validate(user),
                access_token=self.create_access_token(user.id),
            ),
            message="Пользователь успешно зарегистрирован.",
        )

    async def login_user(
        self,
        data: UserLoginRequest,
    ) -> APIResponse[AuthResponse]:
        """
        Проверяет логин и пароль пользователя.

        :param data: Данные для входа пользователя.
        :return: Данные пользователя вместе с токеном сессии или ошибку авторизации.
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

        return APIResponse.success(
            data=AuthResponse(
                user=UserResponse.model_validate(dict(user_row)),
                access_token=self.create_access_token(int(user_row["id"])),
            ),
            message="Вход выполнен успешно.",
        )

    async def get_current_user(self, token: Optional[str]) -> APIResponse[UserResponse]:
        """
        Возвращает текущего пользователя по JWT из заголовка Authorization: Bearer.

        :param token: JWT-токен из заголовка Authorization: Bearer.
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