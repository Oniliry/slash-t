from dependencies.family import CurrentUserDep
from dependencies.notification import NotificationServiceDep
from fastapi import APIRouter, Response

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/me")
async def get_my_notifications(
    user: CurrentUserDep,
    service: NotificationServiceDep,
    response: Response,
):
    """Возвращает персональные и семейные уведомления для текущего пользователя."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return await service.get_notifications(user)


@router.get("/me/advice")
async def get_my_ai_advice(
    user: CurrentUserDep,
    service: NotificationServiceDep,
):
    """Генерирует AI-уведомление отдельно от основной загрузки страницы."""
    return await service.get_ai_advice(user)


__all__ = [
    "router",
]
