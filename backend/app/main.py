#backend/app/main.py

import uvicorn
import os

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from database.init_db import create_tables, drop_tables
from database.base import db

from schemas.base import APIResponse
from routers.auth import router as auth_router
from routers.family import router as family_router
from routers.profile import router as profile_router
from routers.expense import router as expense_router
from routers.debt import router as debt_router
from routers.receipt import router as receipt_router
from routers.notifications import router as notifications_router
from routers.cushion import router as cushion_router
from routers.financial_cushion import router as financial_cushion_router
from routers.slash_t import router as slash_t_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения.

    :param app: Экземпляр FastAPI-приложения.
    """
    await db.connect()

    if os.getenv("RESET_DB", "false").lower() == "true":
        await drop_tables()
    await create_tables()

    yield

    await db.close()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://slasht.ru",
        "https://www.slasht.ru",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(slash_t_router)
app.include_router(auth_router)
app.include_router(family_router)
app.include_router(profile_router)
app.include_router(expense_router)
app.include_router(debt_router)
app.include_router(receipt_router)
app.include_router(notifications_router)
app.include_router(cushion_router)
app.include_router(financial_cushion_router)

@app.get("/health")
async def health():
    """
    Проверяет доступность backend.

    :return: Стандартный успешный ответ API.
    """
    return APIResponse.success(
        message="Сервер работает корректно."
    )

if __name__ == "__main__":
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=not is_production)