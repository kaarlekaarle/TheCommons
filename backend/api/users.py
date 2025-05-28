from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.audit import AuditAction, audit_log, audit_log_decorator
from backend.core.auth import get_current_active_user
from backend.core.exceptions import ResourceNotFoundError, ServerError, ValidationError
from backend.core.logging import get_logger
from backend.database import get_db
from backend.models.user import User
from backend.schemas.user import UserCreate, UserResponse, UserUpdate
from backend.services.user import UserService

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=UserResponse)
@audit_log_decorator(AuditAction.USER_CREATE)
async def create_user(
    user_data: UserCreate, db: AsyncSession = Depends(get_db)
) -> User:
    """Create a new user.

    Args:
        user_data: User creation data
        db: Database session

    Returns:
        User: Created user

    Raises:
        ValidationError: If user data is invalid
        ServerError: If an unexpected error occurs
    """
    user_service = UserService(db)
    try:
        user = await user_service.create_user(user_data)
        return user
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ServerError("Failed to create user")


@router.get("/me", response_model=UserResponse)
@audit_log_decorator(AuditAction.USER_READ)
async def read_user_me(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current user information.

    Args:
        current_user: Currently authenticated user

    Returns:
        User: Current user information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
@audit_log_decorator(AuditAction.USER_UPDATE)
async def update_user_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update current user information.

    Args:
        user_data: Updated user data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        User: Updated user information

    Raises:
        ValidationError: If update data is invalid
        ServerError: If an unexpected error occurs
    """
    user_service = UserService(db)
    try:
        user = await user_service.update_user(current_user.id, user_data)
        return user
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ServerError("Failed to update user")


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
@audit_log_decorator(AuditAction.USER_DELETE)
async def delete_user_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete current user.

    Args:
        current_user: Currently authenticated user
        db: Database session

    Raises:
        ResourceNotFoundError: If user not found
        ServerError: If an unexpected error occurs
    """
    user_service = UserService(db)
    try:
        await user_service.delete_user(current_user.id)
    except Exception as e:
        if isinstance(e, ResourceNotFoundError):
            raise
        raise ServerError("Failed to delete user")
