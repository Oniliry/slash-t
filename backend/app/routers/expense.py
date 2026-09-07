from dependencies.expense import ExpenseServiceDep
from dependencies.family import CurrentUserDep
from fastapi import APIRouter

from schemas.expense import CreateExpenseRequest, UpdateExpenseRequest
from schemas.receipt import ReceiptScanRequest
from services.receipt_service import ReceiptService

router = APIRouter(prefix="/expenses", tags=["expenses"])
receipt_service = ReceiptService()


@router.post("")
async def create_expense(
    data: CreateExpenseRequest,
    user: CurrentUserDep,
    service: ExpenseServiceDep,
):
    """
    Добавляет покупку. В зависимости от того, кому она принадлежит
    (себе / участнику семьи / общая), автоматически создаёт долги перед
    заплатившим пользователем.

    :param data: Сумма покупки, категория и кому она принадлежит.
    :param user: Текущий авторизованный пользователь (плательщик).
    :param service: Сервис для работы с покупками и долгами.
    :return: Данные покупки вместе со списком созданных долгов или ошибку.
    """
    return await service.create_expense(user, data)


@router.get("")
async def list_expenses(
    user: CurrentUserDep,
    service: ExpenseServiceDep,
    limit: int = 50,
):
    """
    Возвращает историю последних покупок семьи — для вкладки «Расходы».

    :param user: Текущий авторизованный пользователь.
    :param service: Сервис для работы с покупками и долгами.
    :param limit: Максимальное количество покупок в ответе.
    :return: Список покупок, отсортированный от новых к старым, или ошибку.
    """
    return await service.list_expenses(user, limit=limit)


@router.post("/receipt/scan")
async def scan_receipt(
    data: ReceiptScanRequest,
    user: CurrentUserDep,
):
    """Распознаёт QR-чек через code-qr.ru для авторизованного пользователя."""
    if user.family_id is None:
        return {
            "error": True,
            "message": "Сначала создайте семью или присоединитесь к ней по коду.",
            "type": "family_required",
        }
    return await receipt_service.scan(data)


@router.put("/{expense_id}")
async def update_expense(
    expense_id: int,
    data: UpdateExpenseRequest,
    user: CurrentUserDep,
    service: ExpenseServiceDep,
):
    """Изменяет покупку и пересчитывает связанные непогашенные долги."""
    return await service.update_expense(user, expense_id, data)


__all__ = [
    "router",
]
