import traceback

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from backend.config import settings
from backend.core.exceptions.base import BaseError




def get_error_response(error: Exception, include_details: bool = False) -> dict:
    if isinstance(error, BaseError):
        response = {
            "code": error.status_code,
            "message": error.message,
        }
        if include_details:
            response["details"] = {
                "type": error.__class__.__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            }
        return response
    return {
        "code": 500,
        "message": "An unexpected error occurred",
        "details": (
            {
                "type": error.__class__.__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            }
            if include_details
            else None
        ),
    }


async def common_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle common exceptions."""
    response = get_error_response(exc, include_details=settings.DEBUG)
    return JSONResponse(
        status_code=response["code"],
        content=response,
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy exceptions."""
    response = get_error_response(exc, include_details=settings.DEBUG)
    return JSONResponse(
        status_code=response["code"],
        content=response,
    )


async def delegation_exception_handler(
    request: Request, exc: BaseError
) -> JSONResponse:
    """Handle delegation-related exceptions."""
    response = get_error_response(exc, include_details=settings.DEBUG)
    return JSONResponse(
        status_code=response["code"],
        content=response,
    )




def configure_exception_handlers(app: FastAPI) -> None:
    """Configure exception handlers for the FastAPI application."""
    # Import delegation exceptions here to avoid circular imports
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

    # Register base exception handlers
    app.add_exception_handler(Exception, common_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(BaseError, delegation_exception_handler)

    # Register delegation-specific exception handlers
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
