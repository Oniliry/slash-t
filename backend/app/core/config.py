#backend/app/core/config.py

from os import getenv
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = getenv(
    "DATABASE_URL",
    "postgresql://slash_t:slash_t@db:5432/slash_t",
)
JWT_SECRET: str = getenv("JWT_SECRET", "local-development-secret-change-me")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(getenv("JWT_EXPIRE_MINUTES", "10080"))


LOGGING_DIR: str = "logging"

RECEIPT_CHECK_API_URL: str = getenv(
    "RECEIPT_CHECK_API_URL",
    "https://proverkacheka.com/api/v1/check/get",
)
RECEIPT_CHECK_API_TOKEN: str = getenv(
    "RECEIPT_CHECK_API_TOKEN",
    "d8c2fe0e-4246e2c4-93b652e8-637cdead",
)

# Распознавание фото чека — сначала пробуем точные данные ФНС по QR-коду
# на чеке (бесплатный сервис proverkacheka.com), если не вышло — GigaChat
# (распознавание по фото) как запасной вариант. GigaChat выбран вместо
# зарубежных нейросетей, чтобы не требовать VPN и работать из России.
RECEIPT_QR_LOOKUP_ENABLED: bool = getenv("RECEIPT_QR_LOOKUP_ENABLED", "1") != "0"

# "Authorization key" из личного кабинета GigaChat API (developers.sber.ru) —
# строка вида "Basic ..." или просто base64-ключ, выданный при создании проекта.
GIGACHAT_AUTH_KEY: str = getenv("GIGACHAT_AUTH_KEY", "")
GIGACHAT_SCOPE: str = getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
# Для распознавания фото нужна модель с поддержкой изображений (vision).
GIGACHAT_MODEL: str = getenv("GIGACHAT_MODEL", "GigaChat-Max")

__all__ = [
    "DATABASE_URL", 
    "JWT_SECRET", 
    "JWT_ALGORITHM",
    "JWT_EXPIRE_MINUTES",
    "LOGGING_DIR",
    "RECEIPT_CHECK_API_URL",
    "RECEIPT_CHECK_API_TOKEN",
    "RECEIPT_QR_LOOKUP_ENABLED",
    "GIGACHAT_AUTH_KEY",
    "GIGACHAT_SCOPE",
    "GIGACHAT_MODEL",
]