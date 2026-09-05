#backend/app/main.py

import uvicorn
import asyncio

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from database.init_db import create_tables, drop_tables
from database.base import db

from schemas.base import APIResponse
from routers.auth import router as auth_router
from routers.slash_t import router as slash_t_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения.

    :param app: Экземпляр FastAPI-приложения.
    """
    await db.connect()
    await create_tables()
    
    yield

    await db.close()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(slash_t_router)
app.include_router(auth_router)

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
    try:
        asyncio.run(drop_tables())
        asyncio.run(create_tables())
    except:
        pass
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)