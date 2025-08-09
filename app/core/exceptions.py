"""Custom exceptions and exception handlers."""
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional

class ErrorResponse(BaseModel):
    """Standard error response format."""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None

class BaseAppException(Exception):
    """Base exception for all application exceptions."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class NotFoundError(BaseAppException):
    """Raised when a resource is not found."""
    def __init__(self, resource: str, identifier: Any, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "id": str(identifier), **(details or {})}
        )

class UnauthorizedError(BaseAppException):
    """Raised when authentication or authorization fails."""
    def __init__(self, message: str = "Not authenticated", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details or {}
        )

class ForbiddenError(BaseAppException):
    """Raised when a user doesn't have permission to access a resource."""
    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details or {}
        )

class ValidationError(BaseAppException):
    """Raised when input validation fails."""
    def __init__(self, message: str = "Validation error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details or {}
        )

class ConflictError(BaseAppException):
    """Raised when there's a conflict with the current state of the resource."""
    def __init__(self, message: str = "Conflict with the current state of the resource", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details or {}
        )

class RateLimitExceededError(BaseAppException):
    """Raised when the rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        headers = {"Retry-After": str(retry_after)} if retry_after else None
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after} if retry_after else {}
        )
        self.headers = headers

async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle HTTP exceptions and return a standardized error response."""
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error="Validation error",
                details={"errors": exc.errors()}
            ).dict()
        )
    
    if isinstance(exc, BaseAppException):
        response = ErrorResponse(
            error=exc.message,
            details=exc.details
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=response.dict(),
            headers=getattr(exc, 'headers', None)
        )
    
    # Log unexpected errors
    request.app.state.logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={
            "path": request.url.path,
            "method": request.method,
            "query_params": dict(request.query_params),
            "client": f"{request.client.host}:{request.client.port}" if request.client else None
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            details={"message": str(exc)} if str(exc) else None
        ).dict()
    )
