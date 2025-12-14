"""
Middleware для обработки ошибок и логирования
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback

from core.exceptions import BaseAppException

logger = logging.getLogger(__name__)


async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Глобальный обработчик исключений
    
    Args:
        request: HTTP запрос
        exc: Исключение
    
    Returns:
        JSON ответ с ошибкой
    """
    # Логируем ошибку
    logger.error(
        f"Необработанное исключение: {type(exc).__name__}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception": str(exc),
            "traceback": traceback.format_exc()
        },
        exc_info=True
    )
    
    # Возвращаем общий ответ об ошибке
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Внутренняя ошибка сервера",
            "type": type(exc).__name__
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Обработчик HTTP исключений
    
    Args:
        request: HTTP запрос
        exc: HTTP исключение
    
    Returns:
        JSON ответ с ошибкой
    """
    logger.warning(
        f"HTTP исключение: {exc.status_code} - {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Обработчик ошибок валидации
    
    Args:
        request: HTTP запрос
        exc: Ошибка валидации
    
    Returns:
        JSON ответ с ошибками валидации
    """
    logger.warning(
        f"Ошибка валидации: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Ошибка валидации данных",
            "errors": exc.errors()
        }
    )


async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """
    Обработчик кастомных исключений приложения
    
    Args:
        request: HTTP запрос
        exc: Кастомное исключение
    
    Returns:
        JSON ответ с ошибкой
    """
    logger.error(
        f"Ошибка приложения: {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

