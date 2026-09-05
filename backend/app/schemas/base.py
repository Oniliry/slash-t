#backend/app/schemas/base.py

from typing import Generic, TypeVar, Optional

from pydantic import BaseModel
from pydantic.config import ConfigDict
from fastapi.responses import JSONResponse

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    """
    Базовая схема возврата информации.
    
    :field error: Флаг ошибки.
    :field message: Описание ошикби.
    :field data: Данные ответа.
    :field type: Тип ошиибки.
    """
    error: bool = False
    message: Optional[str] = None
    data: Optional[T] = {}
    type: Optional[str] = None

    model_config = ConfigDict(
        extra="ignore", 
        populate_by_name=True, 
        exclude_none=True
    )

    @classmethod
    def success(cls, data: T = {}, message: Optional[str] = None) -> "APIResponse[T]":
        """
        Автоматическая генерация успешного ответа.
        
        :param data: Ответ API.
        :param message: Дополнительное сообщение.
        :return: Схема ответа.
        """
        return cls(error=False, data=data, message=message)

    @classmethod
    def fail(cls, message: str, status_code: int = 400, type: Optional[str] = None) -> JSONResponse:
        """
        Автоматическая генерация ответа с ошибкой.
        
        :param message: Сообщение об ошибке.
        :param status_code: Код HTTP-ошибки.
        :param type: Тип ошибки.
        :return: Экземпляр JSONResponse с указанным HTTP-кодом.
        """
        if 199 < status_code < 300:
            raise ValueError("Для данного кода ответа используй метод 'success'")
        
        response = cls(error=True, message=message, type=type)
    
        return JSONResponse(
            status_code=status_code, 
            content=response.model_dump()
        )

    @classmethod
    def warn(cls, message: str, data: Optional[T] = None, status_code: int = 208, type: Optional[str] = None) -> JSONResponse:
        """
        Автоматическая генерация предупреждающего ответа.
        
        :param message: Сообщение-предупреждение.
        :param data: Дополнительные данные.
        :param status_code: Код HTTP-ответа.
        :param type: Тип ошибки.
        :return: Объект JSONResponse с предупреждением.
        """
        if not 199 < status_code < 300 and not 299 < status_code < 400:
            raise ValueError("Для данного кода ответа используй 'success' или 'fail'")
        
        response = cls(error=False, message=message, data=data, status_code=status_code, type=type)
        
        return JSONResponse(
            status_code=status_code, 
            content=response.model_dump()
        )

__all__ = [
    "APIResponse"
]