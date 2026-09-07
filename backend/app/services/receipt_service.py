import asyncio
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from core.config import RECEIPT_API_KEY
from database.models.user import User
from schemas.base import APIResponse
from schemas.receipt import ReceiptScanResponse

#: Базовый URL API code-qr.ru.
PROVIDER_BASE_URL = "https://code-qr.ru/api"

#: Таймаут одного запроса к провайдеру, секунд.
PROVIDER_TIMEOUT = 10

#: Поллинг info: интервал и общий бюджет времени, секунд.
POLL_INTERVAL = 1.5
POLL_BUDGET = 10.0


class ReceiptService:
    """Сервис расшифровки кассовых чеков через code-qr.ru.

    Ключ API хранится в backend .env (RECEIPT_API_KEY) и передаётся
    провайдеру в заголовке key. Фронтенд получает только результат —
    сам ключ наружу не уходит.
    """

    async def scan(self, user: User, qr: str) -> APIResponse:
        """
        Отправляет raw QR чека провайдеру и дожидается результата.

        :param user: Текущий авторизованный пользователь.
        :param qr: Полное содержимое QR-кода чека.
        :return: Хэш чека, статус проверки и сырой ответ провайдера.
        """
        if not RECEIPT_API_KEY:
            return APIResponse.fail(
                message="Сервис проверки чеков не настроен (нет RECEIPT_API_KEY).",
                status_code=503,
                type="receipt_provider_unconfigured",
            )

        try:
            added = await asyncio.to_thread(
                self._request_provider,
                "POST",
                f"{PROVIDER_BASE_URL}/receipt/add-qr",
                data=urlencode({"qr": qr}).encode(),
            )
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            return self._provider_error(exc)

        if not added.get("success"):
            return APIResponse.fail(
                message=added.get("message", "Провайдер отклонил QR чека."),
                status_code=502,
                type="receipt_provider_error",
            )

        receipt_hash = added.get("hash", "")
        if not receipt_hash:
            return APIResponse.fail(
                message="Провайдер не вернул хэш чека.",
                status_code=502,
                type="receipt_provider_error",
            )

        # Проверка чека у провайдера асинхронная: wait -> process -> done.
        # Опрашиваем info, пока не получим финальный статус или не выйдем
        # за бюджет времени — тогда вернём сырой ответ как есть.
        info = {}
        raw_text = json.dumps(added, ensure_ascii=False)
        deadline = time.monotonic() + POLL_BUDGET

        while time.monotonic() < deadline:
            await asyncio.sleep(POLL_INTERVAL)
            try:
                info = await asyncio.to_thread(
                    self._request_provider,
                    "GET",
                    f"{PROVIDER_BASE_URL}/receipt/info?{urlencode({'hash': receipt_hash})}",
                )
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                return self._provider_error(exc)

            raw_text = json.dumps(info, ensure_ascii=False)
            if info.get("status") in ("done", "error"):
                break

        return APIResponse.success(
            ReceiptScanResponse(
                hash=receipt_hash,
                status=info.get("status", "wait"),
                raw=raw_text,
            )
        )

    @staticmethod
    def _request_provider(method: str, url: str, data: bytes | None = None) -> dict:
        """
        Выполняет запрос к code-qr.ru и парсит JSON-ответ.

        :param method: HTTP-метод (GET или POST).
        :param url: Полный URL запроса.
        :param data: Тело запроса (для POST).
        :return: Распарсенный JSON-ответ провайдера.
        """
        request = Request(
            url,
            data=data,
            method=method,
            headers={
                "key": RECEIPT_API_KEY,
                "Accept": "application/json",
            },
        )
        with urlopen(request, timeout=PROVIDER_TIMEOUT) as response:
            return json.loads(response.read().decode())

    @staticmethod
    def _provider_error(exc: Exception) -> APIResponse:
        """Единая ошибка недоступности/сбоя провайдера."""
        return APIResponse.fail(
            message="Сервис проверки чеков недоступен. Попробуйте позже.",
            status_code=502,
            type="receipt_provider_error",
        )


__all__ = [
    "ReceiptService",
]
