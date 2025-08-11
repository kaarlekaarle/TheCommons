from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Unified error response schema for all API endpoints."""
    
    detail: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")
    status_code: int = Field(..., description="HTTP status code")
    error_type: Optional[str] = Field(None, description="Type of error for debugging")
    field: Optional[str] = Field(None, description="Field name if validation error")
    timestamp: Optional[str] = Field(None, description="ISO timestamp of error")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ValidationErrorResponse(ErrorResponse):
    """Specific schema for validation errors."""
    
    field: str = Field(..., description="Field that failed validation")
    value: Optional[Any] = Field(None, description="Invalid value provided")


class AuthenticationErrorResponse(ErrorResponse):
    """Specific schema for authentication errors."""
    
    code: str = Field(default="AUTHENTICATION_ERROR", description="Authentication error code")


class AuthorizationErrorResponse(ErrorResponse):
    """Specific schema for authorization errors."""
    
    code: str = Field(default="AUTHORIZATION_ERROR", description="Authorization error code")


class ResourceNotFoundErrorResponse(ErrorResponse):
    """Specific schema for resource not found errors."""
    
    code: str = Field(default="RESOURCE_NOT_FOUND", description="Resource not found error code")
    resource_type: Optional[str] = Field(None, description="Type of resource that was not found")
    resource_id: Optional[str] = Field(None, description="ID of resource that was not found")


class ConflictErrorResponse(ErrorResponse):
    """Specific schema for conflict errors."""
    
    code: str = Field(default="CONFLICT_ERROR", description="Conflict error code")
    conflicting_field: Optional[str] = Field(None, description="Field causing the conflict")


class ServerErrorResponse(ErrorResponse):
    """Specific schema for server errors."""
    
    code: str = Field(default="INTERNAL_SERVER_ERROR", description="Internal server error code")
    error_id: Optional[str] = Field(None, description="Unique error ID for tracking")


# Error code constants
class ErrorCodes:
    """Standard error codes for the API."""
    
    # Authentication & Authorization
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # Resources
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    
    # Delegation
    DELEGATION_ERROR = "DELEGATION_ERROR"
    CIRCULAR_DELEGATION = "CIRCULAR_DELEGATION"
    SELF_DELEGATION = "SELF_DELEGATION"
    DELEGATION_NOT_FOUND = "DELEGATION_NOT_FOUND"
    DELEGATION_EXPIRED = "DELEGATION_EXPIRED"
    DELEGATION_LIMIT_EXCEEDED = "DELEGATION_LIMIT_EXCEEDED"
    
    # Server
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Health Checks
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"
    REDIS_UNAVAILABLE = "REDIS_UNAVAILABLE"
