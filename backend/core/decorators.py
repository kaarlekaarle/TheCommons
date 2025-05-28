from functools import wraps
from typing import Callable, Dict, Mapping, Optional, Type, TypeVar, cast

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.core.exceptions import (
    AuthorizationError,
    BaseError,
    ConflictError,
    ResourceNotFoundError,
    ServerError,
    ValidationError,
)
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
from backend.core.logging_config import get_logger

logger = get_logger(__name__)

# Type variable for the return type of the decorated function
T = TypeVar("T")

# Default error mapping
DEFAULT_ERROR_MAPPING: Mapping[Type[Exception], tuple[int, str]] = {
    # Database errors
    IntegrityError: (409, "Resource already exists"),
    SQLAlchemyError: (500, "Database error occurred"),
    # Validation errors
    ValueError: (400, "Invalid input"),
    ValidationError: (422, "Validation error"),
    # Resource errors
    ResourceNotFoundError: (404, "Resource not found"),
    AuthorizationError: (403, "Not authorized"),
    ConflictError: (409, "Resource conflict"),
    # Delegation errors
    DelegationError: (400, "Delegation error"),
    DelegationValidationError: (400, "Invalid delegation"),
    SelfDelegationError: (400, "Cannot delegate to yourself"),
    CircularDelegationError: (400, "Circular delegation detected"),
    DelegationNotFoundError: (404, "Delegation not found"),
    DelegationChainError: (400, "Invalid delegation chain"),
    InvalidDelegationPeriodError: (400, "Invalid delegation period"),
    DelegationAlreadyExistsError: (409, "Delegation already exists"),
    DelegationExpiredError: (400, "Delegation has expired"),
    DelegationNotActiveError: (400, "Delegation is not active"),
    DelegationLimitExceededError: (400, "Delegation limit exceeded"),
    DelegationStatsError: (500, "Error calculating delegation statistics"),
}




def handle_errors(
    error_mapping: Optional[Mapping[Type[Exception], tuple[int, str]]] = None,
    default_status: int = 500,
    default_message: str = "An unexpected error occurred",
    log_error: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """A decorator for handling common errors in FastAPI endpoints.

    This decorator provides a standardized way to handle exceptions in FastAPI
    endpoints. It maps specific exception types to appropriate HTTP status codes
    and messages, and provides consistent error logging.

    Args:
        error_mapping: Dictionary mapping exception types to (status_code, message)
            tuples. If None, uses default mapping for common exceptions.
        default_status: Default HTTP status code for unhandled exceptions.
        default_message: Default error message for unhandled exceptions.
        log_error: Whether to log the error.

    Returns:
        Callable: Decorated function with error handling.

    Example:
        @handle_errors({
            IntegrityError: (409, "Resource already exists"),
            ValueError: (400, "Invalid input")
        })
        async def my_endpoint():
            ...
    """
    if error_mapping is None:
        error_mapping = DEFAULT_ERROR_MAPPING

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: tuple, **kwargs: dict) -> T:
            try:
                return await func(*args, **kwargs)
            except BaseError as e:
                # Re-raise our custom exceptions
                raise HTTPException(status_code=e.status_code, detail=e.message)
            except HTTPException:
                # Re-raise FastAPI HTTP exceptions
                raise
            except Exception as e:
                # Find the most specific matching exception
                status_code = default_status
                message = default_message

                for exc_type, (exc_status, exc_message) in error_mapping.items():
                    if isinstance(e, exc_type):
                        status_code = exc_status
                        message = exc_message
                        break

                if log_error:
                    logger.error(
                        "Error in function: %s",
                        func.__name__,
                        extra={
                            "error": str(e),
                            "status_code": status_code,
                            "message": message,
                        },
                        exc_info=True,
                    )

                raise HTTPException(status_code=status_code, detail=message)

        return cast(Callable[..., T], wrapper)

    return decorator
