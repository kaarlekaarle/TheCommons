from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import get_current_active_user
from backend.core.exceptions import (
    AuthorizationError,
    ResourceNotFoundError,
    ValidationError,
)
from backend.core.logging_config import get_logger
from backend.database import get_db
from backend.models.poll import Poll
from backend.models.user import User
from backend.models.vote import Vote
from backend.schemas.poll import Poll as PollSchema
from backend.schemas.poll import PollCreate, PollUpdate, VoteStatus, PollResult
from backend.services.delegation import DelegationService
from backend.services.poll import get_poll_results

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=PollSchema)
async def create_poll(
    poll_data: PollCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Poll:
    """Create a new poll.

    Args:
        poll_data: Poll creation data
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Poll: Created poll

    Raises:
        ValidationError: If poll data is invalid
        ServerError: If an unexpected error occurs
    """
    try:
        poll = Poll(
            title=poll_data.title,
            description=poll_data.description,
            created_by=current_user.id,
        )
        db.add(poll)
        await db.commit()
        await db.refresh(poll)

        # Broadcast new proposal to activity feed
        try:
            from backend.core.websocket import manager
            await manager.broadcast_proposal_created({
                "id": str(poll.id),
                "title": poll.title,
                "description": poll.description,
                "created_by": str(poll.created_by),
                "created_at": poll.created_at.isoformat()
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast proposal creation", extra={"error": str(e)})

        logger.info(
            "Poll created successfully",
            extra={"poll_id": poll.id, "user_id": current_user.id},
        )
        return poll
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        print(f"ERROR creating poll: {e!r}")
        logger.error(
            "Failed to create poll",
            extra={"user_id": current_user.id, "error": str(e)},
            exc_info=True,
        )
        raise ValidationError("Invalid poll data")


@router.get("/", response_model=List[PollSchema])
async def list_polls(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[Poll]:
    """List all polls.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List[Poll]: List of polls
    """
    result = await db.execute(select(Poll).offset(skip).limit(limit))
    polls = result.scalars().all()

    logger.info(
        "Retrieved polls", 
        extra={
            "skip": skip, 
            "limit": limit, 
            "count": len(polls),
            "user_id": current_user.id
        }
    )
    return polls


@router.get("/{poll_id}", response_model=PollSchema)
async def get_poll(
    poll_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Poll:
    """Get a poll by ID.

    Args:
        poll_id: ID of the poll
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Poll: Requested poll with vote status

    Raises:
        ResourceNotFoundError: If poll not found
    """
    from backend.config import settings
    import traceback
    
    logger.info(
        "Starting poll detail request",
        extra={
            "poll_id": str(poll_id),
            "user_id": str(current_user.id),
            "debug": settings.DEBUG,
        },
    )
    
    try:
        # Get poll
        logger.debug("Executing poll query", extra={"poll_id": str(poll_id)})
        result = await db.execute(select(Poll).where(Poll.id == poll_id))
        poll = result.scalar_one_or_none()
        
        if not poll:
            logger.warning("Poll not found", extra={"poll_id": str(poll_id)})
            raise ResourceNotFoundError("Poll not found")
        
        logger.debug("Poll found", extra={"poll_id": str(poll_id), "poll_title": poll.title})

        # Check for direct vote
        logger.debug("Checking for direct vote", extra={"poll_id": str(poll_id), "user_id": str(current_user.id)})
        vote_result = await db.execute(
            select(Vote).where(
                and_(
                    Vote.user_id == current_user.id,
                    Vote.poll_id == poll_id,
                )
            )
        )
        vote = vote_result.scalar_one_or_none()
        
        logger.debug("Vote check result", extra={
            "poll_id": str(poll_id),
            "user_id": str(current_user.id),
            "has_vote": vote is not None,
        })

        # Initialize vote status
        vote_status = VoteStatus(
            status="none",
            resolved_vote_path=[current_user.id],
            final_delegatee_id=current_user.id,
        )

        if vote:
            vote_status.status = "voted"
            logger.debug("User has direct vote", extra={"poll_id": str(poll_id), "user_id": str(current_user.id)})
        else:
            # Check delegation chain
            logger.debug("Checking delegation chain", extra={"poll_id": str(poll_id), "user_id": str(current_user.id)})
            delegation_service = DelegationService(db)
            try:
                final_delegatee = await delegation_service.resolve_delegation_chain(
                    current_user.id, poll_id
                )
                logger.debug("Delegation chain resolved", extra={
                    "poll_id": str(poll_id),
                    "user_id": str(current_user.id),
                    "final_delegatee": str(final_delegatee),
                })
                
                if final_delegatee != current_user.id:
                    vote_status.status = "delegated"
                    vote_status.final_delegatee_id = final_delegatee
                    # TODO: Implement full chain path resolution
                    vote_status.resolved_vote_path.append(final_delegatee)
                    logger.debug("User has delegation", extra={
                        "poll_id": str(poll_id),
                        "user_id": str(current_user.id),
                        "delegated_to": str(final_delegatee),
                    })
            except Exception as e:
                logger.error(
                    "Error in delegation chain resolution",
                    extra={
                        "poll_id": str(poll_id),
                        "user_id": str(current_user.id),
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "traceback": traceback.format_exc() if settings.DEBUG else None,
                    },
                    exc_info=settings.DEBUG,
                )
                # Don't fail the request, just set status to error
                vote_status.status = "error"

        # Add vote status to poll
        poll.your_vote_status = vote_status

        logger.info(
            "Successfully retrieved poll with vote status",
            extra={
                "poll_id": str(poll_id),
                "user_id": str(current_user.id),
                "vote_status": vote_status.status,
            },
        )
        return poll
        
    except ResourceNotFoundError:
        # Re-raise known errors
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in get_poll",
            extra={
                "poll_id": str(poll_id),
                "user_id": str(current_user.id),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc() if settings.DEBUG else None,
            },
            exc_info=settings.DEBUG,
        )
        raise


@router.put("/{poll_id}", response_model=PollSchema)
async def update_poll(
    poll_id: int,
    poll_data: PollUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Poll:
    """Update a poll.

    Args:
        poll_id: ID of the poll to update
        poll_data: Updated poll data
        db: Database session
        current_user: Currently authenticated user

    Returns:
        Poll: Updated poll

    Raises:
        ResourceNotFoundError: If poll not found
        AuthorizationError: If user is not authorized
        ValidationError: If update data is invalid
        ServerError: If an unexpected error occurs
    """
    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalar_one_or_none()
    if not poll:
        logger.warning("Poll not found", extra={"poll_id": poll_id})
        raise ResourceNotFoundError("Poll not found")

    if poll.created_by != current_user.id:
        logger.warning(
            "Unauthorized poll access",
            extra={"poll_id": poll_id, "user_id": current_user.id},
        )
        raise AuthorizationError("Not enough permissions")

    try:
        for field, value in poll_data.dict(exclude_unset=True).items():
            setattr(poll, field, value)

        await db.commit()
        await db.refresh(poll)

        logger.info("Poll updated successfully", extra={"poll_id": poll_id})
        return poll
    except Exception as e:
        logger.error(
            "Failed to update poll",
            extra={"poll_id": poll_id, "error": str(e)},
            exc_info=True,
        )
        raise ValidationError("Invalid update data")


@router.delete("/{poll_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_poll(
    poll_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Delete a poll.

    Args:
        poll_id: ID of the poll to delete
        db: Database session
        current_user: Currently authenticated user

    Raises:
        ResourceNotFoundError: If poll not found
        AuthorizationError: If user is not authorized
        ServerError: If an unexpected error occurs
    """
    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalar_one_or_none()
    if not poll:
        logger.warning("Poll not found", extra={"poll_id": poll_id})
        raise ResourceNotFoundError("Poll not found")

    if poll.created_by != current_user.id:
        logger.warning(
            "Unauthorized poll access",
            extra={"poll_id": poll_id, "user_id": current_user.id},
        )
        raise AuthorizationError("Not enough permissions")

    await db.delete(poll)
    await db.commit()

    logger.info("Poll deleted successfully", extra={"poll_id": poll_id})
    return None


@router.get("/{poll_id}/results", response_model=List[PollResult])
async def get_poll_results_endpoint(
    poll_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[PollResult]:
    """Get poll results with delegation support.

    Args:
        poll_id: ID of the poll
        db: Database session
        current_user: Currently authenticated user

    Returns:
        List[PollResult]: List of poll results with vote counts

    Raises:
        ResourceNotFoundError: If poll not found
        ValidationError: If poll data is invalid
    """
    try:
        results = await get_poll_results(poll_id, db)
        
        logger.info(
            "Retrieved poll results",
            extra={
                "poll_id": poll_id,
                "user_id": current_user.id,
                "results_count": len(results)
            },
        )
        return results
        
    except ValueError as e:
        logger.warning("Poll not found", extra={"poll_id": poll_id})
        raise ResourceNotFoundError(str(e))
    except Exception as e:
        logger.error(
            "Failed to get poll results",
            extra={"poll_id": poll_id, "error": str(e)},
            exc_info=True,
        )
        raise ValidationError("Failed to calculate poll results")
