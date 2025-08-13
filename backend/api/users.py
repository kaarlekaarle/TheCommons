from typing import List, Dict, Any
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from backend.core.audit import AuditAction, audit_log, audit_log_decorator
from backend.core.auth import get_current_active_user
from backend.core.exceptions import ResourceNotFoundError, ServerError, ValidationError, ConflictError
from backend.core.logging_json import get_json_logger, get_request_context
from backend.database import get_db
from backend.models.user import User
from backend.models.poll import Poll
from backend.models.vote import Vote
from backend.models.delegation import Delegation
from backend.models.comment import Comment
from backend.schemas.user import UserCreate, UserResponse, UserUpdate
from backend.services.user import UserService

router = APIRouter()
logger = get_json_logger(__name__)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# @audit_log_decorator(AuditAction.USER_CREATE)  # Temporarily disabled due to decorator issue
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
        ConflictError: If username or email already exists
        ServerError: If an unexpected error occurs
    """
    user_service = UserService(db)
    try:
        user = await user_service.create_user(user_data)
        return user
    except (ValidationError, ConflictError):
        # Let these exceptions propagate with their proper status codes
        raise
    except Exception as e:
        raise ServerError("Failed to create user")


@router.get("/me", response_model=UserResponse)
# @audit_log_decorator(AuditAction.USER_READ)  # Temporarily disabled due to decorator issue
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


@router.delete("/me", status_code=status.HTTP_200_OK)
@audit_log_decorator(AuditAction.USER_DELETE)
async def delete_user_me(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Delete current user (Right to be Forgotten - GDPR compliance).

    Args:
        request: FastAPI request object
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Dict containing summary of deletion actions

    Raises:
        ResourceNotFoundError: If user not found
        ServerError: If an unexpected error occurs
    """
    try:
        # Get request context for logging
        context = get_request_context()
        
        logger.info(
            "User deletion requested (Right to be Forgotten)",
            user_id=str(current_user.id),
            username=current_user.username,
            **context
        )
        
        # Count items that will be affected
        polls_count = await db.execute(
            select(func.count(Poll.id)).where(
                Poll.created_by == current_user.id,
                Poll.is_deleted == False
            )
        )
        polls_count = polls_count.scalar()
        
        votes_count = await db.execute(
            select(func.count(Vote.id)).where(
                Vote.user_id == current_user.id,
                Vote.is_deleted == False
            )
        )
        votes_count = votes_count.scalar()
        
        comments_count = await db.execute(
            select(func.count(Comment.id)).where(
                Comment.user_id == current_user.id,
                Comment.is_deleted == False
            )
        )
        comments_count = comments_count.scalar()
        
        delegations_count = await db.execute(
            select(func.count(Delegation.id)).where(
                (Delegation.delegator_id == current_user.id) | (Delegation.delegatee_id == current_user.id),
                Delegation.is_deleted == False
            )
        )
        delegations_count = delegations_count.scalar()
        
        # Perform soft delete using the user service
        user_service = UserService(db)
        await user_service.delete_user(current_user.id)
        
        # Anonymize user data
        current_user.username = f"deleted_user_{current_user.id}"
        current_user.email = f"deleted_{current_user.id}@deleted.com"
        current_user.hashed_password = "deleted"
        
        await db.commit()
        
        # Prepare deletion summary
        deletion_summary = {
            "message": "User account and associated data have been deleted",
            "deletion_timestamp": datetime.utcnow().isoformat(),
            "request_id": context.get("request_id"),
            "items_deleted": {
                "user_profile": 1,
                "polls_created": polls_count,
                "votes_cast": votes_count,
                "comments_posted": comments_count,
                "delegations": delegations_count,
            },
            "total_items_deleted": 1 + polls_count + votes_count + comments_count + delegations_count,
            "note": "All data has been soft-deleted and user information has been anonymized"
        }
        
        logger.info(
            "User deletion completed (Right to be Forgotten)",
            user_id=str(current_user.id),
            username=current_user.username,
            total_items_deleted=deletion_summary["total_items_deleted"],
            **context
        )
        
        return deletion_summary
        
    except Exception as e:
        logger.error(
            "Failed to delete user",
            user_id=str(current_user.id),
            username=current_user.username,
            error=str(e),
            **context
        )
        if isinstance(e, ResourceNotFoundError):
            raise
        raise ServerError("Failed to delete user")


@router.get("/search/{username}", response_model=UserResponse)
async def search_user_by_username(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Search for a user by username."""
    try:
        result = await db.execute(
            select(User).where(
                and_(
                    User.username == username,
                    User.is_deleted == False
                )
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ResourceNotFoundError(f"User with username '{username}' not found")
        
        return user
    except Exception as e:
        logger.error(
            "Failed to search user by username",
            extra={"username": username, "error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to search user")


@router.get("/me/export")
async def export_user_data(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Export all data for the current user (GDPR compliance).
    
    Args:
        request: FastAPI request object
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Dict containing all user data
    """
    try:
        # Get request context for logging
        context = get_request_context()
        
        logger.info(
            "User data export requested",
            user_id=str(current_user.id),
            username=current_user.username,
            **context
        )
        
        # Export user profile
        user_data = {
            "profile": {
                "id": str(current_user.id),
                "username": current_user.username,
                "email": current_user.email,
                "is_active": current_user.is_active,
                "is_superuser": current_user.is_superuser,
                "email_verified": current_user.email_verified,
                "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
                "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
                "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            }
        }
        
        # Export polls created by user
        polls_result = await db.execute(
            select(Poll).where(
                Poll.created_by == current_user.id,
                Poll.is_deleted == False
            ).order_by(Poll.created_at.desc())
        )
        polls = polls_result.scalars().all()
        
        user_data["polls"] = [
            {
                "id": str(poll.id),
                "title": poll.title,
                "description": poll.description,
                "created_at": poll.created_at.isoformat() if poll.created_at else None,
                "updated_at": poll.updated_at.isoformat() if poll.updated_at else None,
                "is_active": poll.is_active,
                "total_votes": poll.total_votes,
            }
            for poll in polls
        ]
        
        # Export votes by user
        votes_result = await db.execute(
            select(Vote).where(
                Vote.user_id == current_user.id,
                Vote.is_deleted == False
            ).order_by(Vote.created_at.desc())
        )
        votes = votes_result.scalars().all()
        
        user_data["votes"] = [
            {
                "id": str(vote.id),
                "poll_id": str(vote.poll_id),
                "option_id": str(vote.option_id),
                "created_at": vote.created_at.isoformat() if vote.created_at else None,
                "updated_at": vote.updated_at.isoformat() if vote.updated_at else None,
            }
            for vote in votes
        ]
        
        # Export delegations where user is delegator
        delegations_as_delegator_result = await db.execute(
            select(Delegation).where(
                Delegation.delegator_id == current_user.id,
                Delegation.is_deleted == False
            ).order_by(Delegation.created_at.desc())
        )
        delegations_as_delegator = delegations_as_delegator_result.scalars().all()
        
        user_data["delegations_as_delegator"] = [
            {
                "id": str(delegation.id),
                "poll_id": str(delegation.poll_id),
                "delegatee_id": str(delegation.delegatee_id),
                "delegatee_username": delegation.delegatee.username if delegation.delegatee else None,
                "created_at": delegation.created_at.isoformat() if delegation.created_at else None,
                "updated_at": delegation.updated_at.isoformat() if delegation.updated_at else None,
            }
            for delegation in delegations_as_delegator
        ]
        
        # Export delegations where user is delegatee
        delegations_as_delegatee_result = await db.execute(
            select(Delegation).where(
                Delegation.delegatee_id == current_user.id,
                Delegation.is_deleted == False
            ).order_by(Delegation.created_at.desc())
        )
        delegations_as_delegatee = delegations_as_delegatee_result.scalars().all()
        
        user_data["delegations_as_delegatee"] = [
            {
                "id": str(delegation.id),
                "poll_id": str(delegation.poll_id),
                "delegator_id": str(delegation.delegator_id),
                "delegator_username": delegation.delegator.username if delegation.delegator else None,
                "created_at": delegation.created_at.isoformat() if delegation.created_at else None,
                "updated_at": delegation.updated_at.isoformat() if delegation.updated_at else None,
            }
            for delegation in delegations_as_delegatee
        ]
        
        # Export comments by user
        comments_result = await db.execute(
            select(Comment).where(
                Comment.user_id == current_user.id,
                Comment.is_deleted == False
            ).order_by(Comment.created_at.desc())
        )
        comments = comments_result.scalars().all()
        
        user_data["comments"] = [
            {
                "id": str(comment.id),
                "poll_id": str(comment.poll_id),
                "body": comment.body,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
                "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
            }
            for comment in comments
        ]
        
        # Add export metadata
        user_data["export_metadata"] = {
            "exported_at": datetime.utcnow().isoformat(),
            "request_id": context.get("request_id"),
            "total_polls": len(user_data["polls"]),
            "total_votes": len(user_data["votes"]),
            "total_delegations_as_delegator": len(user_data["delegations_as_delegator"]),
            "total_delegations_as_delegatee": len(user_data["delegations_as_delegatee"]),
            "total_comments": len(user_data["comments"]),
        }
        
        logger.info(
            "User data export completed",
            user_id=str(current_user.id),
            username=current_user.username,
            total_polls=len(user_data["polls"]),
            total_votes=len(user_data["votes"]),
            total_comments=len(user_data["comments"]),
            **context
        )
        
        return user_data
        
    except Exception as e:
        logger.error(
            "Failed to export user data",
            user_id=str(current_user.id),
            username=current_user.username,
            error=str(e),
            **context
        )
        raise ServerError("Failed to export user data")
