"""
Кастомные исключения для приложения
"""
from fastapi import HTTPException, status


class BaseAppException(Exception):
    """Базовое исключение приложения"""
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class NotFoundError(BaseAppException):
    """Ресурс не найден"""
    def __init__(self, resource: str, identifier: str = None):
        detail = f"{resource} не найден"
        if identifier:
            detail += f" (ID: {identifier})"
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class ValidationError(BaseAppException):
    """Ошибка валидации"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class AuthenticationError(BaseAppException):
    """Ошибка аутентификации"""
    def __init__(self, detail: str = "Не удалось подтвердить учетные данные"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(BaseAppException):
    """Ошибка авторизации"""
    def __init__(self, detail: str = "Недостаточно прав"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class ExternalServiceError(BaseAppException):
    """Ошибка внешнего сервиса"""
    def __init__(self, service: str, detail: str = None):
        detail = detail or f"Ошибка при обращении к {service}"
        super().__init__(detail=detail, status_code=status.HTTP_502_BAD_GATEWAY)

