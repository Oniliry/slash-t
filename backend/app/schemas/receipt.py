from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


class ReceiptScanRequest(BaseModel):
    """QR-строка чека, считанная камерой телефона."""

    qr: str = Field(min_length=1, max_length=4000)


class ReceiptItemResponse(BaseModel):
    """Товар, распознанный сервисом проверки чека."""

    name: str
    quantity: Decimal
    price: Decimal
    amount: Decimal


class ReceiptResponse(BaseModel):
    """Нормализованный результат проверки чека."""

    hash: str
    date: str
    total: Decimal
    store: str
    items: List[ReceiptItemResponse]


__all__ = ["ReceiptItemResponse", "ReceiptResponse", "ReceiptScanRequest"]
