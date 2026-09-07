from dependencies.family import CurrentUserDep
from dependencies.receipt import ReceiptServiceDep
from fastapi import APIRouter
from schemas.receipt import ParseReceiptPhotoRequest

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.post("/parse-photo")
async def parse_receipt_photo(
    data: ParseReceiptPhotoRequest,
    user: CurrentUserDep,
    service: ReceiptServiceDep,
):
    """
    Распознаёт товары на фото чека через локальный OCR — для мобильной загрузки фото.

    :param data: Фото чека в base64 и его MIME-тип.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис распознавания чеков.
    :return: Распознанные позиции чека или сообщение об ошибке.
    """
    return await service.parse_photo(data.image_base64, data.mime_type)


__all__ = [
    "router",
]
