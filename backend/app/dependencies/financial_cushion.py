from typing import Annotated

from fastapi import Depends

from database.base import db
from database.repositories import CushionAnalysisRepository
from services.financial_cushion_service import FinancialCushionService


def get_cushion_analysis_repo() -> CushionAnalysisRepository:
    """
    Создаёт репозиторий сохранённых анализов выписок.

    :return: Репозиторий анализов с общим подключением к БД.
    """
    return CushionAnalysisRepository(db)


def get_financial_cushion_service(
    analysis_repo: CushionAnalysisRepository = Depends(get_cushion_analysis_repo),
) -> FinancialCushionService:
    """
    Создаёт сервис анализа выписок.

    :param analysis_repo: Репозиторий анализов, предоставленный FastAPI.
    :return: Сервис анализа PDF-выписок и пересчёта финподушки.
    """
    return FinancialCushionService(analysis_repo)


FinancialCushionServiceDep = Annotated[
    FinancialCushionService, Depends(get_financial_cushion_service)
]


__all__ = [
    "FinancialCushionServiceDep",
]
