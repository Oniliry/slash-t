from typing import Annotated

from fastapi import Depends

from services.receipt_service import ReceiptService


def get_receipt_service() -> ReceiptService:
    """
    Создаёт сервис расшифровки кассовых чеков.

    :return: Сервис проверки чеков через code-qr.ru.
    """
    return ReceiptService()


ReceiptServiceDep = Annotated[ReceiptService, Depends(get_receipt_service)]


__all__ = [
    "get_receipt_service",
    "ReceiptServiceDep",
]
