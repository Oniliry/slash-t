#backend/app/main.py

import asyncio
import uvicorn

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from database.init_db import create_tables
from database.base import db

from schemas.base import APIResponse
from routers.slash_t import router as slash_t_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управляет жизненным циклом приложения."""
    await db.connect()
    
    yield

    await db.close()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(slash_t_router)

@app.get("/health")
async def health():
    """Проверка состояния приложения."""
    return APIResponse.success(
        message="Сервер работает корректно."
    )

if __name__ == "__main__":
    asyncio.run(create_tables())
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)