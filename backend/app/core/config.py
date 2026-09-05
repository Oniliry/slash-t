#backend/app/core/config.py

from os import getenv
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError(
            "Пожалуйста, установите DATABASE_URL в .env файлe."
        )
    
LOGGING_DIR: str = "logging"

__all__ = [
    "DATABASE_URL"
]