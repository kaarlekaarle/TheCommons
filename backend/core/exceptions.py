import traceback
from typing import Any, Dict, Optional, Type, TypedDict, Union

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from backend.config import settings
from backend.core.exceptions.base import (
    AuthenticationError,
    AuthorizationError,
    BaseError,
    ConflictError,
    DatabaseError,
    ResourceNotFoundError,
    ServerError,
    UserAlreadyExistsError,
    ValidationError,
)




class ErrorDetails(TypedDict, total=False):
    """Error details for API responses."""

    field: str
    message: str
    code: str
    value: Any




class ErrorResponse(TypedDict, total=False):
    """Standard error response format."""

    error: str
    message: str
    details: list[ErrorDetails]
    code: str
    status_code: int




class CommonException(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[list[ErrorDetails]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or []
        super().__init__(message)

    def to_dict(self) -> ErrorResponse:
        """Convert exception to dictionary format."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "code": self.error_code or self.__class__.__name__,
            "status_code": self.status_code,
        }


async def common_exception_handler(
    request: Request, exc: CommonException
) -> JSONResponse:
    """Handle common exceptions.

    Args:
        request: FastAPI request object
        exc: The exception that occurred

    Returns:
        JSONResponse: Error response with status code and detail
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy exceptions.

    Args:
        request: FastAPI request object
        exc: The SQLAlchemy exception that occurred

    Returns:
        JSONResponse: Error response with 500 status code
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred"},
    )


async def delegation_exception_handler(
    request: Request, exc: BaseError
) -> JSONResponse:
    """Handle delegation-related exceptions.

    Args:
        request: FastAPI request object
        exc: The delegation exception that occurred

    Returns:
        JSONResponse: Error response with appropriate status code and details
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=get_error_response(exc, include_details=settings.DEBUG),
    )




def configure_exception_handlers(app: FastAPI) -> None:
    """Configure exception handlers for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Register base exception handlers
    app.add_exception_handler(CommonException, common_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(BaseError, delegation_exception_handler)

    # Add handlers for all delegation-related exceptions
    from backend.core.exceptions.delegation import (
        CircularDelegationError,
        DelegationAlreadyExistsError,
        DelegationChainError,
        DelegationError,
        DelegationExpiredError,
        DelegationLimitExceededError,
        DelegationNotActiveError,
        DelegationNotFoundError,
        DelegationStatsError,
        DelegationValidationError,
        InvalidDelegationPeriodError,
        SelfDelegationError,
    )

    delegation_exceptions = [
        DelegationError,
        DelegationValidationError,
        SelfDelegationError,
        CircularDelegationError,
        DelegationNotFoundError,
        DelegationChainError,
        InvalidDelegationPeriodError,
        DelegationAlreadyExistsError,
        DelegationExpiredError,
        DelegationNotActiveError,
        DelegationLimitExceededError,
        DelegationStatsError,
    ]

    for exc in delegation_exceptions:
        app.add_exception_handler(exc, delegation_exception_handler)




def get_error_response(
    error: Exception, include_details: bool = False
) -> Dict[str, ErrorResponse]:
    """Get a standardized error response.

    Args:
        error: The exception that occurred
        include_details: Whether to include detailed error information

    Returns:
        Dict[str, ErrorResponse]: Standardized error response
    """
    if isinstance(error, BaseError):
        response = {
            "error": error.__class__.__name__,
            "message": error.message,
            "details": [
                {
                    "field": "type",
                    "message": error.__class__.__name__,
                    "code": error.error_code or error.__class__.__name__,
                    "value": str(error),
                }
            ],
            "code": error.error_code or error.__class__.__name__,
            "status_code": error.status_code,
        }
        if include_details:
            response["details"].append({
                "field": "traceback",
                "message": traceback.format_exc(),
                "code": "traceback",
                "value": traceback.format_exc(),
            })
        return response

    return {
        "error": error.__class__.__name__,
        "message": "An unexpected error occurred",
        "details": [
            {
                "field": "type",
                "message": error.__class__.__name__,
                "code": "unknown",
                "value": str(error),
            }
        ],
        "code": "unknown",
        "status_code": 500,
    }
