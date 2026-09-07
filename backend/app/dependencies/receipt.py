from typing import Annotated

from fastapi import Depends

from services.receipt_service import ReceiptService


def get_receipt_service() -> ReceiptService:
    """
    Создаёт сервис распознавания чеков.

    :return: Сервис для обращения к Gemini.
    """
    return ReceiptService()


ReceiptServiceDep = Annotated[ReceiptService, Depends(get_receipt_service)]


__all__ = [
    "ReceiptServiceDep",
]
