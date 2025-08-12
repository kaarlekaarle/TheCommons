from typing import Any, Dict, Optional

from fastapi import status




class BaseError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        return f"{self.message} (Status: {self.status_code})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary format."""
        return {
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }




class ValidationError(BaseError):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=400, details=details)




class ResourceNotFoundError(BaseError):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=404, details=details)




class ServerError(BaseError):
    """Raised when an unexpected server error occurs."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)




class ConflictError(BaseError):
    """Raised when a resource conflict occurs."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=409, details=details)




class AuthorizationError(BaseError):
    """Raised when a user is not authorized to perform an action."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=403, details=details)




class AuthenticationError(BaseError):
    """Raised when authentication fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=401, details=details)


class UnavailableFeatureError(BaseError):
    """Raised when a feature is disabled or unavailable."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=403, details=details)




class UserAlreadyExistsError(ConflictError):
    """Raised when attempting to create a user that already exists."""

    def __init__(
        self,
        message: str = "User already exists",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details=details)




class DatabaseError(BaseError):
    """Database related errors."""

    def __init__(self, detail: str = "Database error occurred") -> None:
        super().__init__(
            message=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"detail": detail},
        )
