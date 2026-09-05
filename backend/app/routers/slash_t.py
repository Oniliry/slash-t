from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from dependencies.slash_t import get_slash_t_service
from services.slash_t_service import SlashTService

router = APIRouter(prefix="/slash-t", tags=["slash-t"])


@router.get("", response_class=PlainTextResponse)
async def get_slash_t(service: SlashTService = Depends(get_slash_t_service)) -> str:
    return service.get_text()


__all__ = [
    "router",
]