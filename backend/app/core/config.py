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
JWT_COOKIE_NAME: str = "slash_t_access_token"
JWT_COOKIE_SECURE: bool = getenv("ENVIRONMENT", "development") == "production"


LOGGING_DIR: str = "logging"

__all__ = [
    "DATABASE_URL", 
    "JWT_SECRET", 
    "JWT_ALGORITHM",
    "JWT_EXPIRE_MINUTES",
    "JWT_COOKIE_NAME",
    "JWT_COOKIE_SECURE",
]