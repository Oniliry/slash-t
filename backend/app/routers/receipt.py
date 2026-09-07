from dependencies.family import CurrentUserDep
from dependencies.receipt import ReceiptServiceDep
from fastapi import APIRouter

from schemas.receipt import ScanReceiptRequest

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.post("/scan")
async def scan_receipt(
    data: ScanReceiptRequest,
    user: CurrentUserDep,
    service: ReceiptServiceDep,
):
    """
    Принимает raw-строку из QR-кода кассового чека, отправляет её
    в сервис проверки чеков (code-qr.ru) и возвращает сырой ответ.

    :param data: Содержимое QR-кода чека без изменений.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис расшифровки чеков.
    :return: Хэш чека, статус проверки и raw-строка ответа провайдера.
    """
    return await service.scan(user, data.qr)


__all__ = [
    "router",
]
