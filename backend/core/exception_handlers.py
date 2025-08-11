import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from backend.config import settings
from backend.core.exceptions.base import BaseError
from backend.schemas.error import (
    AuthenticationErrorResponse,
    AuthorizationErrorResponse,
    ConflictErrorResponse,
    ErrorCodes,
    ErrorResponse,
    ResourceNotFoundErrorResponse,
    ServerErrorResponse,
    ValidationErrorResponse,
)


def get_error_response(
    error: Exception, 
    include_details: bool = False,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Generate unified error response."""
    
    # Get request ID for tracing
    error_id = str(uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Base error response
    response = {
        "detail": str(error),
        "status_code": 500,
        "error_type": error.__class__.__name__,
        "timestamp": timestamp,
        "request_id": request_id,
        "error_id": error_id,
    }
    
    # Handle custom BaseError exceptions
    if isinstance(error, BaseError):
        response.update({
            "detail": error.message,
            "status_code": error.status_code,
            "code": _get_error_code(error),
        })
        
        # Add specific error details
        if hasattr(error, 'details') and error.details:
            response["details"] = error.details
            
        # Add field-specific info for validation errors
        if isinstance(error, BaseError) and hasattr(error, 'field'):
            response["field"] = error.field
            
    # Handle specific exception types
    elif isinstance(error, ValueError):
        response.update({
            "detail": str(error),
            "status_code": 400,
            "code": ErrorCodes.VALIDATION_ERROR,
        })
    elif isinstance(error, SQLAlchemyError):
        response.update({
            "detail": "Database error occurred",
            "status_code": 500,
            "code": ErrorCodes.DATABASE_ERROR,
        })
    else:
        response.update({
            "detail": "An unexpected error occurred",
            "status_code": 500,
            "code": ErrorCodes.INTERNAL_SERVER_ERROR,
        })
    
    # Add debug details in development
    if include_details:
        response["details"] = {
            "type": error.__class__.__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
    
    return response


def _get_error_code(error: BaseError) -> str:
    """Map BaseError types to error codes."""
    error_type = error.__class__.__name__
    
    code_mapping = {
        "ValidationError": ErrorCodes.VALIDATION_ERROR,
        "ResourceNotFoundError": ErrorCodes.RESOURCE_NOT_FOUND,
        "AuthorizationError": ErrorCodes.AUTHORIZATION_ERROR,
        "AuthenticationError": ErrorCodes.AUTHENTICATION_ERROR,
        "ConflictError": ErrorCodes.RESOURCE_CONFLICT,
        "ServerError": ErrorCodes.INTERNAL_SERVER_ERROR,
        "UserAlreadyExistsError": ErrorCodes.RESOURCE_ALREADY_EXISTS,
        "DatabaseError": ErrorCodes.DATABASE_ERROR,
    }
    
    # Handle delegation-specific errors
    if "Delegation" in error_type:
        if "Circular" in error_type:
            return ErrorCodes.CIRCULAR_DELEGATION
        elif "Self" in error_type:
            return ErrorCodes.SELF_DELEGATION
        elif "NotFound" in error_type:
            return ErrorCodes.DELEGATION_NOT_FOUND
        elif "Expired" in error_type:
            return ErrorCodes.DELEGATION_EXPIRED
        elif "Limit" in error_type:
            return ErrorCodes.DELEGATION_LIMIT_EXCEEDED
        else:
            return ErrorCodes.DELEGATION_ERROR
    
    return code_mapping.get(error_type, ErrorCodes.INTERNAL_SERVER_ERROR)


async def common_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle common exceptions with unified response format."""
    request_id = getattr(request.state, "request_id", None)
    response = get_error_response(exc, include_details=settings.DEBUG, request_id=request_id)
    
    return JSONResponse(
        status_code=response["status_code"],
        content=response,
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy exceptions with unified response format."""
    request_id = getattr(request.state, "request_id", None)
    response = get_error_response(exc, include_details=settings.DEBUG, request_id=request_id)
    
    return JSONResponse(
        status_code=response["status_code"],
        content=response,
    )


async def delegation_exception_handler(
    request: Request, exc: BaseError
) -> JSONResponse:
    """Handle delegation-related exceptions with unified response format."""
    request_id = getattr(request.state, "request_id", None)
    response = get_error_response(exc, include_details=settings.DEBUG, request_id=request_id)
    
    return JSONResponse(
        status_code=response["status_code"],
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
