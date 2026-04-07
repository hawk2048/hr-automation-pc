"""Error handling and HTTP exception classes"""
from fastapi import HTTPException, status
from typing import Optional, Any


class AppError(Exception):
    """Base application error"""
    def __init__(
        self, 
        message: str, 
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found"""
    def __init__(self, resource: str, id: Any):
        super().__init__(
            f"{resource} not found: {id}",
            code="NOT_FOUND",
            status_code=404
        )


class ValidationError(AppError):
    """Validation error"""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details
        )


class UnauthorizedError(AppError):
    """Unauthorized access"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message,
            code="UNAUTHORIZED",
            status_code=401
        )


class ForbiddenError(AppError):
    """Forbidden access"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message,
            code="FORBIDDEN",
            status_code=403
        )


class ConflictError(AppError):
    """Resource conflict"""
    def __init__(self, message: str):
        super().__init__(
            message,
            code="CONFLICT",
            status_code=409
        )


def http_exception(status_code: int, message: str):
    """Create HTTP exception from status code"""
    return HTTPException(
        status_code=status_code,
        detail=message
    )


async def app_error_handler(request, exc: AppError):
    """Global error handler for AppError"""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )


async def generic_error_handler(request, exc: Exception):
    """Global error handler for unexpected errors"""
    from fastapi.responses import JSONResponse
    import logging
    logging.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred"
        }
    )