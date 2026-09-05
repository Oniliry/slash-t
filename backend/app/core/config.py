#backend/app/core/config.py

from os import getenv
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = getenv("DATABASE_URL")
JWT_SECRET: str = getenv("JWT_SECRET", "local-development-secret-change-me")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(getenv("JWT_EXPIRE_MINUTES", "10080"))

if DATABASE_URL is None:
    raise ValueError(
            "Пожалуйста, установите DATABASE_URL в .env файлe."
        )
    
LOGGING_DIR: str = "logging"

__all__ = [
    "DATABASE_URL"
    , "JWT_SECRET"
    , "JWT_ALGORITHM"
    , "JWT_EXPIRE_MINUTES"
]