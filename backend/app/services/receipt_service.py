import base64
import json
import re
import time
import uuid
from io import BytesIO
from typing import List, Optional

import httpx
from PIL import Image
from pyzbar.pyzbar import decode as decode_qr_codes

from core.config import (
    GIGACHAT_AUTH_KEY,
    GIGACHAT_MODEL,
    GIGACHAT_SCOPE,
    RECEIPT_CHECK_API_TOKEN,
    RECEIPT_CHECK_API_URL,
    RECEIPT_QR_LOOKUP_ENABLED,
)
from schemas.base import APIResponse
from schemas.receipt import ParsedReceiptItem, ParsedReceiptResponse

# Ключевые слова для авто-категоризации по названию товара (используются
# только для позиций из ФНС по QR — GigaChat на фото классифицирует сама).
# Порядок важен: первое совпадение побеждает.
_CATEGORY_KEYWORDS = [
    ("cafe", ["кофе", "кафе", "ресторан", "бургер", "пицц", "суши", "шаурм"]),
    (
        "transport",
        ["бензин", "азс", "топливо", "метро", "такси", "проезд", "автобус"],
    ),
    (
        "health",
        ["аптека", "лекарств", "таблет", "витамин", "аскорбин", "клиник"],
    ),
    ("utilities", ["жкх", "коммунал", "электро", "интернет", "связь", "мтс", "билайн", "мегафон"]),
    ("clothing", ["одежд", "обувь", "футболк", "джинс", "куртк"]),
    (
        "entertainment",
        ["кино", "театр", "концерт", "игра", "боулинг", "квест"],
    ),
    (
        "groceries",
        [
            "молок", "хлеб", "яйц", "мясо", "куриц", "рыб", "сыр", "масл",
            "овощ", "фрукт", "картоф", "морков", "лук", "яблок", "банан",
            "крупа", "рис", "макарон", "сахар", "соль", "чай", "вод",
            "йогурт", "творог", "колбас", "сосиск", "конфет", "шоколад",
        ],
    ),
]

# Товары, которые считаются личными покупками, а не общими
# (используется только для позиций из ФНС по QR).
_PERSONAL_KEYWORDS = [
    "пиво", "вино", "водка", "виски", "коньяк", "шампанск",
    "сигарет", "табак", "vape", "вейп",
    "духи", "парфюм", "косметик", "помада", "тушь", "крем для лица",
    "наушник", "зарядк", "кабель", "флешк",
]

_ALLOWED_CATEGORIES = [
    "groceries", "utilities", "transport", "cafe",
    "entertainment", "health", "clothing", "other",
]

_GIGACHAT_OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
_GIGACHAT_API_BASE = "https://gigachat.devices.sberbank.ru/api/v1"

# GigaChat использует сертификат российского удостоверяющего центра
# (Минцифры), которого нет в стандартных доверенных корнях большинства
# окружений, поэтому проверку TLS-сертификата для этого хоста отключаем.
# Для продакшена правильнее один раз установить сертификат Минцифры в
# систему и убрать verify=False — так безопаснее, но сложнее в настройке.
_GIGACHAT_VERIFY_SSL = False

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)

_GIGACHAT_PROMPT = """Ты распознаёшь товарный чек по фотографии для семейного \
финансового приложения.

Найди на фото название магазина (если видно) и список купленных позиций. \
Для каждой позиции определи:
- name — название товара (коротко, разборчиво);
- sum — стоимость позиции целиком в рублях (если на чеке указаны отдельно \
цена за штуку и количество — верни их произведение, итоговую сумму по строке);
- category — одна из категорий: groceries (продукты), utilities (жкх/связь), \
transport (топливо/проезд), cafe (кафе/рестораны/доставка еды), \
entertainment (развлечения), health (аптека/здоровье), clothing (одежда/обувь), \
other (всё остальное);
- personal — true, если это алкоголь, сигареты/табак/вейп, косметика/парфюмерия \
или техника/аксессуары (наушники, кабели, зарядки и т.п.) — такие покупки \
считаются личными, а не общими семейными; для всех остальных товаров — false.

Не включай в items строки итогов, скидок, реквизитов, номеров чека/кассы — \
только реально купленные товары.

Ответь СТРОГО одним JSON-объектом без markdown-разметки (без ```), без \
пояснений до или после, ровно в таком формате:
{"shop": "Название магазина или null", "items": [{"name": "...", "sum": 0.00, \
"category": "groceries", "personal": false}]}"""


class _GigaChatTokenCache:
    """Простой кэш OAuth-токена GigaChat (не даёт запрашивать новый на каждый чек)."""

    def __init__(self) -> None:
        self._token: Optional[str] = None
        self._expires_at: float = 0.0

    async def get(self) -> Optional[str]:
        """
        Возвращает действующий access-токен GigaChat, при необходимости
        обновляя его через OAuth.

        :return: Токен доступа или None, если GIGACHAT_AUTH_KEY не задан
            либо сервис авторизации GigaChat недоступен.
        """
        if not GIGACHAT_AUTH_KEY:
            return None

        # Обновляем заранее (за минуту до истечения), чтобы не ловить 401
        # прямо посреди запроса на распознавание.
        if self._token and time.time() < self._expires_at - 60:
            return self._token

        try:
            async with httpx.AsyncClient(timeout=15, verify=_GIGACHAT_VERIFY_SSL) as client:
                response = await client.post(
                    _GIGACHAT_OAUTH_URL,
                    headers={
                        "Authorization": f"Basic {GIGACHAT_AUTH_KEY}",
                        "RqUID": str(uuid.uuid4()),
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data={"scope": GIGACHAT_SCOPE},
                )
                payload = response.json()
        except Exception:
            return None

        token = payload.get("access_token")
        if not token:
            return None

        # expires_at от GigaChat приходит в миллисекундах Unix-времени.
        expires_at_ms = payload.get("expires_at")
        self._expires_at = (expires_at_ms / 1000) if expires_at_ms else time.time() + 1500
        self._token = token
        return token


_giga_token_cache = _GigaChatTokenCache()


class ReceiptService:
    """
    Сервис распознавания чеков.

    Сначала пытаемся получить точные данные напрямую от ФНС по QR-коду на
    чеке (бесплатный сервис proverkacheka.com) — это не распознавание, а
    чтение официального фискального документа, поэтому названия и суммы
    товаров всегда верны. Если QR не найден/не пробит или сервис недоступен —
    используем GigaChat (распознавание по фото) как запасной вариант: он
    работает без VPN из России и сам же классифицирует товары по категориям.
    """

    async def parse_photo(
        self,
        image_base64: str,
        mime_type: str,
    ) -> APIResponse[ParsedReceiptResponse]:
        """
        Распознаёт товары на фото чека: сначала через QR-код (точные данные
        ФНС), при неудаче — через GigaChat.

        :param image_base64: Фото чека в base64.
        :param mime_type: MIME-тип фото (image/jpeg, image/png и т.д.).
        :return: Распознанные позиции чека либо сообщение об ошибке.
        """
        try:
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image_bytes))
        except Exception:
            return APIResponse.fail(
                message="Не удалось открыть фото. Попробуйте другой файл.",
                status_code=422,
                type="receipt_bad_image",
            )

        if RECEIPT_QR_LOOKUP_ENABLED:
            qr_result = await self._lookup_by_qr(image)
            if qr_result is not None:
                return APIResponse.success(
                    data=qr_result,
                    message="Чек распознан по QR-коду — данные ФНС, товары точны.",
                )

        return await self._parse_with_gigachat(image_bytes, mime_type)

    async def _lookup_by_qr(self, image: Image.Image) -> Optional[ParsedReceiptResponse]:
        """
        Ищет QR-код на фото чека и, если находит, запрашивает точные данные
        фискального документа через proverkacheka.com.

        :param image: Открытое изображение чека.
        :return: Точные позиции чека из ФНС или None, если QR не найден,
            не распознан либо сервис не смог его пробить.
        """
        qr_text = self._decode_qr(image)
        if not qr_text:
            return None

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    RECEIPT_CHECK_API_URL,
                    data={"token": RECEIPT_CHECK_API_TOKEN, "qrraw": qr_text},
                )
                payload = response.json()
        except Exception:
            return None

        try:
            document = payload["data"]["json"]
            raw_items = document["items"]
        except (KeyError, TypeError):
            return None

        items: List[ParsedReceiptItem] = []
        for raw_item in raw_items:
            name = str(raw_item.get("name", "")).strip()
            if not name:
                continue
            amount = raw_item.get("sum")
            if amount is None:
                price = raw_item.get("price", 0)
                quantity = raw_item.get("quantity", 1)
                amount = price * quantity
            try:
                amount = round(float(amount) / 100 if float(amount) > 100_000 else float(amount), 2)
            except (TypeError, ValueError):
                continue
            if amount <= 0:
                continue

            category, personal = self._classify(name)
            items.append(ParsedReceiptItem(name=name, sum=amount, category=category, personal=personal))

        if not items:
            return None

        shop = document.get("retailPlace") or document.get("user") or None
        return ParsedReceiptResponse(shop=shop, items=items)

    @staticmethod
    def _decode_qr(image: Image.Image) -> Optional[str]:
        """
        Пытается найти и раскодировать QR-код на фото (пробует исходный
        размер и увеличенную версию — на фото со смартфона код часто мелкий).

        :param image: Открытое изображение чека.
        :return: Сырая строка QR-кода (t=...&s=...&fn=...&i=...&fp=...&n=...) или None.
        """
        candidates = [image.convert("L")]
        if image.width < 1600:
            scale = 1600 / image.width
            candidates.append(
                candidates[0].resize((int(image.width * scale), int(image.height * scale)), Image.LANCZOS)
            )

        for candidate in candidates:
            try:
                found = decode_qr_codes(candidate)
            except Exception:
                continue
            for code in found:
                try:
                    text = code.data.decode("utf-8")
                except Exception:
                    continue
                if "fn=" in text and "fp=" in text:
                    return text
        return None

    async def _parse_with_gigachat(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> APIResponse[ParsedReceiptResponse]:
        """
        Запасной путь: распознаёт товары на фото чека через GigaChat (Сбер) —
        доступен из России без VPN, сама модель классифицирует товары по
        категориям.

        :param image_bytes: Фото чека (сырые байты).
        :param mime_type: MIME-тип фото.
        :return: Распознанные позиции чека либо сообщение об ошибке.
        """
        token = await _giga_token_cache.get()
        if not token:
            return APIResponse.fail(
                message="Распознавание фото временно недоступно. Добавьте позиции чека вручную.",
                status_code=500,
                type="receipt_ai_not_configured",
            )

        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with httpx.AsyncClient(timeout=30, verify=_GIGACHAT_VERIFY_SSL) as client:
                # GigaChat принимает изображения только через отдельную загрузку
                # файла (получаем file_id), а не как inline-base64 в самом чате.
                upload_response = await client.post(
                    f"{_GIGACHAT_API_BASE}/files",
                    headers=headers,
                    files={"file": ("receipt.jpg", image_bytes, mime_type)},
                    data={"purpose": "general"},
                )
                file_payload = upload_response.json()
                file_id = file_payload.get("id")
                if not file_id:
                    return APIResponse.fail(
                        message="Не удалось загрузить фото в сервис распознавания. Попробуйте ещё раз.",
                        status_code=502,
                        type="receipt_ai_unavailable",
                    )

                chat_response = await client.post(
                    f"{_GIGACHAT_API_BASE}/chat/completions",
                    headers=headers,
                    json={
                        "model": GIGACHAT_MODEL,
                        "messages": [
                            {
                                "role": "user",
                                "content": _GIGACHAT_PROMPT,
                                "attachments": [file_id],
                            },
                        ],
                        "temperature": 0.1,
                    },
                )
                chat_payload = chat_response.json()
        except Exception:
            return APIResponse.fail(
                message="Не удалось связаться с сервисом распознавания. Попробуйте ещё раз.",
                status_code=502,
                type="receipt_ai_unavailable",
            )

        try:
            raw_text = chat_payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return APIResponse.fail(
                message="Не удалось распознать товары на фото. Попробуйте переснять чек "
                "при хорошем освещении, без бликов, или добавьте позиции вручную.",
                status_code=422,
                type="receipt_not_recognized",
            )

        parsed = self._extract_json(raw_text)
        if parsed is None:
            return APIResponse.fail(
                message="Не удалось распознать товары на фото. Попробуйте переснять чек "
                "при хорошем освещении, без бликов, или добавьте позиции вручную.",
                status_code=422,
                type="receipt_not_recognized",
            )

        items: List[ParsedReceiptItem] = []
        for raw_item in parsed.get("items", []):
            name = str(raw_item.get("name", "")).strip()
            if not name:
                continue
            try:
                amount = round(float(raw_item.get("sum", 0)), 2)
            except (TypeError, ValueError):
                continue
            if amount <= 0:
                continue

            category = raw_item.get("category")
            if category not in _ALLOWED_CATEGORIES:
                category = "other"
            personal = bool(raw_item.get("personal", False))

            items.append(ParsedReceiptItem(name=name, sum=amount, category=category, personal=personal))

        if not items:
            return APIResponse.fail(
                message="Не удалось найти позиции на чеке. Попробуйте переснять чек ровно, "
                "без наклона, при хорошем освещении — или сфотографируйте QR-код на чеке крупнее.",
                status_code=422,
                type="receipt_not_recognized",
            )

        shop = parsed.get("shop")
        shop = str(shop).strip()[:100] if shop else None

        return APIResponse.success(
            data=ParsedReceiptResponse(shop=shop, items=items),
            message="Чек распознан.",
        )

    @staticmethod
    def _extract_json(raw_text: str) -> Optional[dict]:
        """
        Достаёт JSON-объект из ответа GigaChat: модель иногда всё равно
        оборачивает JSON в markdown-блок ```json ... ``` или добавляет
        пояснение рядом, несмотря на просьбу в промпте так не делать.

        :param raw_text: Сырой текстовый ответ модели.
        :return: Разобранный словарь или None, если JSON найти не удалось.
        """
        try:
            return json.loads(raw_text)
        except (TypeError, ValueError):
            pass

        match = _JSON_BLOCK_RE.search(raw_text or "")
        if not match:
            return None

        try:
            return json.loads(match.group(0))
        except ValueError:
            return None

    @classmethod
    def _classify(cls, name: str) -> tuple[str, bool]:
        """
        Определяет категорию расхода и признак "личное" по названию товара.
        Используется только для позиций, полученных из ФНС по QR — GigaChat
        на фото классифицирует товары сама.

        :param name: Название товара.
        :return: Кортеж (код категории, personal).
        """
        lowered = name.lower()
        category = "other"
        for code, keywords in _CATEGORY_KEYWORDS:
            if any(keyword in lowered for keyword in keywords):
                category = code
                break

        personal = any(keyword in lowered for keyword in _PERSONAL_KEYWORDS)
        return category, personal


__all__ = [
    "ReceiptService",
]
