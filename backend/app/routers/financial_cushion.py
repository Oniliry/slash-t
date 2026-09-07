from dependencies.family import CurrentUserDep
from dependencies.financial_cushion import FinancialCushionServiceDep
from fastapi import APIRouter, UploadFile

from schemas.financial_cushion import StatementRecalculateRequest

router = APIRouter(prefix="/financial-cushion", tags=["financial-cushion"])


@router.post("/upload-statement")
async def upload_statement(
    file: UploadFile,
    user: CurrentUserDep,
    service: FinancialCushionServiceDep,
):
    """
    Принимает PDF-выписку Сбербанка, прогоняет её через готовый
    алгоритм financial_cushion и сохраняет результат за текущим
    пользователем.

    :param file: PDF-файл выписки (multipart/form-data).
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис анализа выписок.
    :return: Разобранный JSON: месяцы, транзакции, кандидаты-переводы.
    """
    return await service.upload_statement(user, file)


@router.post("/recalculate")
async def recalculate_statement(
    data: StatementRecalculateRequest,
    user: CurrentUserDep,
    service: FinancialCushionServiceDep,
):
    """
    Пересчитывает финансовую подушку по правкам пользователя:
    флаги is_active у трат, включение переводов в подушку и их названия.

    :param data: Изменённый пользователем JSON транзакций.
    :param user: Текущий авторизованный пользователь.
    :param service: Сервис анализа выписок.
    :return: Пересчитанный итог и группы расходов.
    """
    return await service.recalculate(user, data)


@router.get("/last")
async def get_last_analysis(
    user: CurrentUserDep,
    service: FinancialCushionServiceDep,
):
    """
    Возвращает последний анализ выписки текущего пользователя.

    :param user: Текущий авторизованный пользователь.
    :param service: Сервис анализа выписок.
    :return: Сохранённый JSON анализа или data: null.
    """
    return await service.get_last(user)


@router.get("/family-summary")
async def get_family_summary(
    user: CurrentUserDep,
    service: FinancialCushionServiceDep,
):
    """
    Возвращает рейтинг участников семьи по убыванию финподушки.

    :param user: Текущий авторизованный пользователь.
    :param service: Сервис анализа выписок.
    :return: Список участников: имя, сумма подушки, число месяцев.
    """
    return await service.family_summary(user)


@router.delete("/last")
async def reset_last_analysis(
    user: CurrentUserDep,
    service: FinancialCushionServiceDep,
):
    """
    Удаляет сохранённый анализ текущего пользователя (кнопка «Сбросить»).

    :param user: Текущий авторизованный пользователь.
    :param service: Сервис анализа выписок.
    :return: Пустой успешный ответ.
    """
    return await service.reset(user)


__all__ = [
    "router",
]
