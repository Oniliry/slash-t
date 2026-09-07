from typing import List, Optional

from pydantic import BaseModel, Field


class ParseReceiptPhotoRequest(BaseModel):
    """
    Схема запроса на распознавание фото чека.

    :field image_base64: Содержимое фото в base64 (без префикса data:...).
    :field mime_type: MIME-тип фото (image/jpeg, image/png и т.д.).
    """

    image_base64: str = Field(min_length=1)
    mime_type: str = Field(default="image/jpeg", max_length=50)


class ParsedReceiptItem(BaseModel):
    """
    Схема одной позиции, распознанной Gemini на фото чека.

    :field name: Название товара.
    :field sum: Стоимость позиции целиком, в рублях.
    :field category: Категория расхода — один из существующих кодов
        категорий покупки (groceries/utilities/transport/cafe/
        entertainment/health/clothing/other).
    :field personal: True, если товар — алкоголь, сигареты, косметика или
        техника (по правилу команды такие покупки личные, а не общие).
    """

    name: str
    sum: float
    category: str = "other"
    personal: bool = False


class ParsedReceiptResponse(BaseModel):
    """
    Схема ответа с позициями, распознанными на фото чека.

    :field shop: Название магазина, если Gemini смогла его разобрать.
    :field items: Список распознанных позиций.
    """

    shop: Optional[str] = None
    items: List[ParsedReceiptItem] = Field(default_factory=list)


__all__ = [
    "ParseReceiptPhotoRequest",
    "ParsedReceiptItem",
    "ParsedReceiptResponse",
]
