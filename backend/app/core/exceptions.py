"""
Global exception handlers for the FastAPI application.
Provides consistent error responses across the API.
"""

from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Error detail model."""

    field: Optional[str] = None
    message: str
    type: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""

    success: bool = False
    error_code: str
    message: str
    details: Optional[list[ErrorDetail]] = None
    request_id: Optional[str] = None


class APIException(Exception):
    """Base API exception."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[list[Dict[str, Any]]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class NotFoundException(APIException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found", details: Optional[list[Dict[str, Any]]] = None):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ValidationException(APIException):
    """Validation error exception."""

    def __init__(self, message: str = "Validation error", details: Optional[list[Dict[str, Any]]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class AuthenticationException(APIException):
    """Authentication error exception."""

    def __init__(self, message: str = "Authentication failed", details: Optional[list[Dict[str, Any]]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class AuthorizationException(APIException):
    """Authorization error exception."""

    def __init__(self, message: str = "Permission denied", details: Optional[list[Dict[str, Any]]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ConflictException(APIException):
    """Resource conflict exception."""

    def __init__(self, message: str = "Resource conflict", details: Optional[list[Dict[str, Any]]] = None):
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class QuotaExceededException(APIException):
    """Quota exceeded exception (rate limiting / billing)."""

    def __init__(
        self,
        message: str = "Monthly quota exceeded",
        retry_after: Optional[int] = None,
        details: Optional[list[Dict[str, Any]]] = None
    ):
        super().__init__(
            message=message,
            error_code="QUOTA_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )
        self.retry_after = retry_after


def get_request_id(request: Request) -> Optional[str]:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", None)


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom API exceptions."""
    error_details = [
        ErrorDetail(
            field=detail.get("field"),
            message=detail.get("message", ""),
            type=detail.get("type"),
        )
        for detail in exc.details
    ] if exc.details else None

    response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        details=error_details,
        request_id=get_request_id(request),
    )

    headers = {}
    if isinstance(exc, QuotaExceededException) and exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(exclude_none=True),
        headers=headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        details.append(
            ErrorDetail(
                field=field,
                message=error.get("msg", ""),
                type=error.get("type"),
            )
        )

    response = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details=details,
        request_id=get_request_id(request),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(exclude_none=True),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    import traceback
    traceback.print_exc()

    response = ErrorResponse(
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        request_id=get_request_id(request),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(exclude_none=True),
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI application."""
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
