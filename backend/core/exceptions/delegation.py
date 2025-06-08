from typing import Any, Dict, Optional
from uuid import UUID

from backend.core.exceptions import BaseError, ResourceNotFoundError, ValidationError




class DelegationError(BaseError):
    """Base class for delegation-related errors."""

    def __init__(
        self,
        message: str,
        delegator_id: Optional[UUID] = None,
        delegatee_id: Optional[UUID] = None,
        poll_id: Optional[UUID] = None,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.delegator_id = delegator_id
        self.delegatee_id = delegatee_id
        self.poll_id = poll_id
        super().__init__(message, status_code=status_code, details=details)




class DelegationValidationError(DelegationError):
    """Raised when delegation validation fails."""

    def __init__(
        self,
        message: str = "Invalid delegation",
        delegator_id: Optional[UUID] = None,
        delegatee_id: Optional[UUID] = None,
        poll_id: Optional[UUID] = None,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            delegator_id=delegator_id,
            delegatee_id=delegatee_id,
            poll_id=poll_id,
            status_code=status_code,
            details=details,
        )




class SelfDelegationError(DelegationValidationError):
    """Raised when a user attempts to delegate to themselves."""

    def __init__(
        self,
        user_id: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
    ) -> None:
        message = f"User {user_id} cannot delegate to themselves"
        super().__init__(
            message=message,
            details=details or {"user_id": user_id},
            status_code=status_code,
        )




class ExistingDelegationError(DelegationError):
    """Error raised when a user already has an active delegation."""

    def __init__(
        self,
        delegator_id: UUID,
        poll_id: Optional[UUID] = None,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        scope = f"for poll {poll_id}" if poll_id else "globally"
        super().__init__(
            f"User {delegator_id} already has an active delegation {scope}",
            delegator_id=delegator_id,
            poll_id=poll_id,
            status_code=status_code,
            details=details,
        )




class CircularDelegationError(DelegationValidationError):
    """Raised when a circular delegation is detected."""

    def __init__(
        self,
        user_id: str,
        delegate_id: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
    ):
        message = (
            f"Circular delegation detected between users {user_id} and {delegate_id}"
        )
        super().__init__(
            message=message,
            details=details or {"user_id": user_id, "delegate_id": delegate_id},
            status_code=status_code,
        )




class PostVoteDelegationError(DelegationError):
    """Error raised when a user tries to delegate after voting."""

    def __init__(
        self,
        user_id: UUID,
        poll_id: UUID,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            f"User {user_id} cannot delegate for poll {poll_id} after voting",
            delegator_id=user_id,
            poll_id=poll_id,
            status_code=status_code,
            details=details,
        )




class DelegationNotFoundError(DelegationError):
    """Error raised when a delegation is not found."""

    def __init__(
        self,
        delegation_id: UUID,
        status_code: int = 404,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            f"Delegation {delegation_id} not found",
            delegator_id=None,
            delegatee_id=None,
            status_code=status_code,
            details=details,
        )




class DelegationChainError(DelegationError):
    """Error raised when there's an issue with the delegation chain."""

    def __init__(
        self,
        message: str,
        user_id: UUID,
        poll_id: Optional[UUID] = None,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            delegator_id=user_id,
            poll_id=poll_id,
            status_code=status_code,
            details=details,
        )




class InvalidDelegationPeriodError(DelegationValidationError):
    """Raised when the delegation period is invalid."""

    def __init__(
        self,
        message: str = "Invalid delegation period",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
    ):
        super().__init__(message=message, details=details, status_code=status_code)




class DelegationAlreadyExistsError(DelegationValidationError):
    """Raised when attempting to create a delegation that already exists."""

    def __init__(
        self,
        user_id: str,
        delegate_id: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
    ):
        message = f"Delegation from user {user_id} to {delegate_id} already exists"
        super().__init__(
            message=message,
            details=details or {"user_id": user_id, "delegate_id": delegate_id},
            status_code=status_code,
        )




class DelegationExpiredError(DelegationValidationError):
    """Raised when attempting to use an expired delegation."""

    def __init__(
        self,
        delegation_id: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
    ):
        message = f"Delegation {delegation_id} has expired"
        super().__init__(
            message=message,
            details=details or {"delegation_id": delegation_id},
            status_code=status_code,
        )




class DelegationNotActiveError(DelegationValidationError):
    """Raised when attempting to use an inactive delegation."""

    def __init__(
        self,
        delegation_id: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
    ) -> None:
        message = f"Delegation {delegation_id} is not active"
        super().__init__(
            message=message,
            details=details or {"delegation_id": delegation_id},
            status_code=status_code,
        )




class DelegationLimitExceededError(DelegationValidationError):
    """Raised when a user has exceeded their delegation limit."""

    def __init__(
        self,
        user_id: str,
        limit: int,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
    ):
        message = f"User {user_id} has exceeded their delegation limit of {limit}"
        super().__init__(
            message=message,
            details=details or {"user_id": user_id, "limit": limit},
            status_code=status_code,
        )




class DelegationStatsError(DelegationError):
    """Raised when there's an error calculating delegation statistics."""

    def __init__(
        self,
        message: str = "Error calculating delegation statistics",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, status_code=status_code, details=details)




class DelegationAuthorizationError(DelegationError):
    """Raised when a user is not authorized to perform a delegation action."""

    def __init__(
        self,
        message: str = "Not authorized to perform this delegation action",
        delegator_id: Optional[UUID] = None,
        delegatee_id: Optional[UUID] = None,
        poll_id: Optional[UUID] = None,
        status_code: int = 403,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            delegator_id=delegator_id,
            delegatee_id=delegatee_id,
            poll_id=poll_id,
            status_code=status_code,
            details=details,
        )
