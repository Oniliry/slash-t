import asyncio
import json
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from core.config import CODE_QR_API_KEY
from schemas.base import APIResponse
from schemas.receipt import ReceiptItemResponse, ReceiptResponse, ReceiptScanRequest

_API_BASE = "https://code-qr.ru/api/receipt"
_POLL_INTERVAL_SECONDS = 2
_POLL_ATTEMPTS = 30


def _decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value).replace(" ", "").replace(",", "."))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Некорректное поле {field_name} в ответе code-qr.ru.") from exc


def _request_json(url: str, method: str = "GET", data: bytes | None = None) -> Dict[str, Any]:
    if not CODE_QR_API_KEY:
        raise RuntimeError("Не задан CODE_QR_API_KEY на сервере.")

    request = Request(
        url,
        data=data,
        method=method,
        headers={
            "key": CODE_QR_API_KEY,
            "Accept": "application/json",
            **({"Content-Type": "application/x-www-form-urlencoded"} if data else {}),
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"code-qr.ru вернул HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError("Не удалось связаться с code-qr.ru.") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("code-qr.ru вернул неожиданный формат ответа.")
    return payload


def _submit_qr(qr: str) -> str:
    payload = _request_json(
        f"{_API_BASE}/add-qr",
        method="POST",
        data=urlencode({"qr": qr}).encode("utf-8"),
    )
    if not payload.get("success") or not payload.get("hash"):
        raise ValueError(payload.get("message") or "code-qr.ru не принял QR-код чека.")
    return str(payload["hash"])


def _get_receipt(receipt_hash: str) -> Dict[str, Any]:
    return _request_json(f"{_API_BASE}/info?{urlencode({'hash': receipt_hash})}")


def _normalize_receipt(receipt_hash: str, payload: Dict[str, Any]) -> ReceiptResponse:
    result = payload.get("result") or {}
    raw_items = result.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("В ответе code-qr.ru отсутствует список товаров.")

    items: List[ReceiptItemResponse] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict) or not raw_item.get("name"):
            continue
        items.append(
            ReceiptItemResponse(
                name=str(raw_item["name"]),
                quantity=_decimal(raw_item.get("quantity", 1), "quantity"),
                price=_decimal(raw_item.get("price", raw_item.get("sum", 0)), "price"),
                amount=_decimal(raw_item.get("sum", 0), "sum"),
            )
        )

    if not items:
        raise ValueError("В чеке не найдено товаров.")

    return ReceiptResponse(
        hash=receipt_hash,
        date=str(payload.get("t") or ""),
        total=_decimal(payload.get("s", 0), "s"),
        store=str(result.get("user") or "Магазин"),
        items=items,
    )


class ReceiptService:
    """Интеграция с code-qr.ru без раскрытия API-ключа клиенту."""

    async def scan(self, data: ReceiptScanRequest) -> APIResponse[ReceiptResponse]:
        try:
            receipt_hash = await asyncio.to_thread(_submit_qr, data.qr)
            for _ in range(_POLL_ATTEMPTS):
                payload = await asyncio.to_thread(_get_receipt, receipt_hash)
                status = payload.get("status")
                if status == "done":
                    return APIResponse.success(
                        _normalize_receipt(receipt_hash, payload),
                        message="Чек распознан.",
                    )
                if status == "error":
                    return APIResponse.fail(
                        payload.get("error") or "code-qr.ru не смог проверить чек.",
                        status_code=422,
                        type="receipt_processing_error",
                    )
                await asyncio.sleep(_POLL_INTERVAL_SECONDS)
        except (RuntimeError, ValueError) as exc:
            return APIResponse.fail(str(exc), status_code=502, type="receipt_provider_error")

        return APIResponse.fail(
            "Проверка чека занимает слишком много времени. Попробуйте ещё раз.",
            status_code=504,
            type="receipt_timeout",
        )


__all__ = ["ReceiptService"]
