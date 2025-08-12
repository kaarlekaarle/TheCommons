from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security, status, Request
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import get_current_active_user, oauth2_scheme
from backend.core.exceptions import (
    AuthorizationError,
    ResourceNotFoundError,
    ServerError,
    ValidationError,
)
from backend.core.logging_config import get_logger
from backend.core.audit_mw import audit_event
from backend.core.voting import (
    cast_vote,
    create_vote,
    delete_vote,
    get_vote,
    update_vote,
)
from backend.database import get_db
from backend.models.user import User
from backend.models.vote import Vote
from backend.schemas.vote import Vote as VoteSchema
from backend.schemas.vote import VoteCreate, VoteUpdate

logger = get_logger(__name__)
router = APIRouter(tags=["votes"])

# Log all available routes
for route in router.routes:
    logger.info(f"Available route: {route.path} [{route.methods}]")


@router.post("/", response_model=VoteSchema, status_code=status.HTTP_201_CREATED)
async def create_new_vote(
    request: Request,
    vote_in: VoteCreate,
    token: str = Depends(oauth2_scheme),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Vote:
    """Create a new vote.

    Args:
        vote_in: Vote creation data
        token: OAuth2 token
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Vote: Created vote

    Raises:
        ValidationError: If vote data is invalid
        ServerError: If an unexpected error occurs
    """
    logger.info(
        "Creating new vote",
        extra={"vote_data": vote_in.model_dump(), "user_id": current_user.id},
    )
    try:
        vote = await create_vote(db, vote_in.model_dump(), current_user)
        
        # Broadcast vote update
        try:
            from backend.core.websocket import manager
            await manager.broadcast_vote_update(str(vote.poll_id), {
                "id": str(vote.id),
                "poll_id": str(vote.poll_id),
                "option_id": str(vote.option_id),
                "user_id": str(vote.user_id),
                "created_at": vote.created_at.isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast vote creation", extra={"error": str(e)})
        
        logger.info(
            "Vote created successfully",
            extra={"vote_id": vote.id, "user_id": current_user.id},
        )
        
        # Audit the vote creation
        audit_event(
            "vote_cast",
            {
                "vote_id": str(vote.id),
                "poll_id": str(vote.poll_id),
                "option_id": str(vote.option_id),
            },
            request
        )
        
        return vote
    except ValueError as e:
        logger.warning(
            "Vote creation failed - validation error",
            extra={"user_id": current_user.id, "error": str(e)},
        )
        raise ValidationError(str(e))
    except Exception as e:
        logger.error(
            "Failed to create vote",
            extra={"user_id": current_user.id, "error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to create vote")


@router.get("/", response_model=List[VoteSchema])
async def list_votes(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[Vote]:
    """List all votes.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List[Vote]: List of votes

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view all votes",
        )
    result = await db.execute(select(Vote).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/poll/{poll_id}/my-vote", response_model=VoteSchema)
async def get_my_vote_for_poll(
    poll_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Vote:
    """Get the current user's vote for a specific poll.

    Args:
        poll_id: ID of the poll
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Vote: User's vote for the poll

    Raises:
        ResourceNotFoundError: If vote not found
    """
    result = await db.execute(
        select(Vote).where(
            Vote.poll_id == poll_id,
            Vote.user_id == current_user.id,
            Vote.is_deleted == False
        )
    )
    vote = result.scalar_one_or_none()
    if not vote:
        raise HTTPException(status_code=404, detail="Vote not found")
    return vote


@router.get("/{vote_id}", response_model=VoteSchema)
async def get_vote(
    vote_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Vote:
    """Get a vote by ID.

    Args:
        vote_id: ID of the vote
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Vote: Requested vote

    Raises:
        ResourceNotFoundError: If vote not found
        AuthorizationError: If user is not authorized
    """
    result = await db.execute(select(Vote).where(Vote.id == vote_id))
    vote = result.scalar_one_or_none()
    if not vote:
        raise HTTPException(status_code=404, detail="Vote not found")
    if not current_user.is_admin and vote.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this vote",
        )
    return vote


@router.put("/{vote_id}", response_model=VoteSchema)
@router.patch("/{vote_id}", response_model=VoteSchema)
async def update_existing_vote(
    vote_id: UUID,
    vote_in: VoteUpdate,
    token: str = Depends(oauth2_scheme),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Vote:
    """Update a vote.

    Args:
        vote_id: ID of the vote to update
        vote_in: Updated vote data
        token: OAuth2 token
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Vote: Updated vote

    Raises:
        ResourceNotFoundError: If vote not found
        AuthorizationError: If user is not vote creator
        ValidationError: If update data is invalid
        ServerError: If an unexpected error occurs
    """
    logger.info(
        "Updating vote",
        extra={
            "vote_id": vote_id,
            "vote_data": vote_in.model_dump(),
            "user_id": current_user.id,
        },
    )
    try:
        vote = await update_vote(
            db, vote_id, vote_in.model_dump(exclude_unset=True), current_user
        )
        logger.info(
            "Vote updated successfully",
            extra={"vote_id": vote_id, "user_id": current_user.id},
        )
        return vote
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            logger.warning(
                "Vote not found", extra={"vote_id": vote_id, "user_id": current_user.id}
            )
            raise ResourceNotFoundError(error_msg)
        elif "not authorized" in error_msg.lower():
            logger.warning(
                "Unauthorized vote access",
                extra={"vote_id": vote_id, "user_id": current_user.id},
            )
            raise AuthorizationError(error_msg)
        logger.error(
            "Invalid vote update data",
            extra={"vote_id": vote_id, "user_id": current_user.id, "error": error_msg},
        )
        raise ValidationError(error_msg)
    except Exception as e:
        logger.error(
            "Failed to update vote",
            extra={"vote_id": vote_id, "user_id": current_user.id, "error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to update vote")


@router.delete("/{vote_id}", response_model=VoteSchema)
async def delete_existing_vote(
    vote_id: UUID,
    token: str = Depends(oauth2_scheme),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Vote:
    """Delete a vote.

    Args:
        vote_id: ID of the vote to delete
        token: OAuth2 token
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Vote: Deleted vote

    Raises:
        ResourceNotFoundError: If vote not found
        AuthorizationError: If user is not vote creator
        ServerError: If an unexpected error occurs
    """
    logger.info("Deleting vote", extra={"vote_id": vote_id, "user_id": current_user.id})
    try:
        vote = await delete_vote(db, vote_id, current_user)
        logger.info(
            "Vote deleted successfully",
            extra={"vote_id": vote_id, "user_id": current_user.id},
        )
        return vote
    except ValueError as e:
        logger.warning(
            "Vote not found", extra={"vote_id": vote_id, "user_id": current_user.id}
        )
        raise ResourceNotFoundError(str(e))
    except Exception as e:
        logger.error(
            "Failed to delete vote",
            extra={"vote_id": vote_id, "user_id": current_user.id, "error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to delete vote")


@router.post("/{vote_id}/cast", response_model=VoteSchema)
async def cast_new_vote(
    vote_id: UUID,
    token: str = Depends(oauth2_scheme),
    current_user: User = Security(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Vote:
    """Cast a vote.

    Args:
        vote_id: ID of the vote to cast
        token: OAuth2 token
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Vote: Cast vote

    Raises:
        ResourceNotFoundError: If vote not found
        ValidationError: If vote cannot be cast
        ServerError: If an unexpected error occurs
    """
    logger.info("Casting vote", extra={"vote_id": vote_id, "user_id": current_user.id})
    try:
        vote = await cast_vote(db, vote_id, current_user)
        logger.info(
            "Vote cast successfully",
            extra={"vote_id": vote_id, "user_id": current_user.id},
        )
        return vote
    except ValueError as e:
        logger.warning(
            "Vote not found", extra={"vote_id": vote_id, "user_id": current_user.id}
        )
        raise ResourceNotFoundError(str(e))
    except Exception as e:
        logger.error(
            "Failed to cast vote",
            extra={"vote_id": vote_id, "user_id": current_user.id, "error": str(e)},
            exc_info=True,
        )
        raise ServerError("Failed to cast vote")
