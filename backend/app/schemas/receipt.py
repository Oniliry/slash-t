"""DTO сканирования QR-кодов кассовых чеков."""

from pydantic import BaseModel, Field


class ScanReceiptRequest(BaseModel):
    """Raw-строка из QR-кода чека (например, t=...&s=...&fn=...&i=...&fp=...)."""

    #: Полное содержимое QR-кода без изменений.
    qr: str = Field(min_length=4)


class ReceiptScanResponse(BaseModel):
    """Результат обработки QR чека внешним сервисом code-qr.ru.

    raw содержит исходный текст JSON-ответа провайдера — фронтенд
    показывает его на экране результата как есть.
    """

    #: Хэш чека у провайдера (для последующих запросов info).
    hash: str
    #: Статус проверки у провайдера: wait / process / done / error.
    status: str
    #: Исходный JSON-ответ провайдера в виде строки.
    raw: str


__all__ = [
    "ScanReceiptRequest",
    "ReceiptScanResponse",
]
