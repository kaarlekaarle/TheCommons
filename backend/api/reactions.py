"""Comment reactions API endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import get_current_active_user
from backend.core.logging_json import get_json_logger
from backend.database import get_db
from backend.models.comment import Comment
from backend.models.comment_reaction import CommentReaction, ReactionType
from backend.models.user import User
from backend.schemas.reaction import ReactionIn, ReactionResponse, ReactionSummary
from backend.core.websocket import manager

router = APIRouter()
logger = get_json_logger(__name__)


async def get_comment_reaction_counts(comment_id: UUID, db: AsyncSession) -> tuple[int, int]:
    """Get reaction counts for a comment."""
    up_count_result = await db.execute(
        select(func.count(CommentReaction.id)).where(
            CommentReaction.comment_id == comment_id,
            CommentReaction.type == ReactionType.UP
        )
    )
    up_count = up_count_result.scalar() or 0
    
    down_count_result = await db.execute(
        select(func.count(CommentReaction.id)).where(
            CommentReaction.comment_id == comment_id,
            CommentReaction.type == ReactionType.DOWN
        )
    )
    down_count = down_count_result.scalar() or 0
    
    return up_count, down_count


async def get_user_reaction(comment_id: UUID, user_id: UUID, db: AsyncSession) -> Optional[ReactionType]:
    """Get user's reaction for a comment."""
    result = await db.execute(
        select(CommentReaction).where(
            CommentReaction.comment_id == comment_id,
            CommentReaction.user_id == user_id
        )
    )
    reaction = result.scalar_one_or_none()
    return reaction.type if reaction else None


@router.post("/{comment_id}/reactions", response_model=ReactionResponse)
async def set_comment_reaction(
    comment_id: UUID,
    reaction_data: ReactionIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReactionResponse:
    """Set or update a reaction on a comment.
    
    Args:
        comment_id: The comment ID
        reaction_data: The reaction data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated reaction counts and user's reaction
        
    Raises:
        HTTPException: If comment not found
    """
    # Verify comment exists
    comment_result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.is_deleted == False)
    )
    comment = comment_result.scalar_one_or_none()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Get existing reaction
    existing_reaction_result = await db.execute(
        select(CommentReaction).where(
            CommentReaction.comment_id == comment_id,
            CommentReaction.user_id == current_user.id
        )
    )
    existing_reaction = existing_reaction_result.scalar_one_or_none()
    
    # Handle upsert logic
    if existing_reaction:
        if existing_reaction.type.value == reaction_data.type:
            # Same type - remove reaction (toggle off)
            await db.delete(existing_reaction)
            my_reaction = None
        else:
            # Different type - update reaction
            existing_reaction.type = ReactionType(reaction_data.type)
            my_reaction = reaction_data.type
    else:
        # No existing reaction - create new one
        new_reaction = CommentReaction(
            comment_id=comment_id,
            user_id=current_user.id,
            type=ReactionType(reaction_data.type)
        )
        db.add(new_reaction)
        my_reaction = reaction_data.type
    
    await db.commit()
    
    # Get updated counts
    up_count, down_count = await get_comment_reaction_counts(comment_id, db)
    
    # Broadcast to WebSocket
    try:
        await manager.broadcast_to_room(
            f"proposal:{comment.poll_id}",
            {
                "type": "comment_reaction",
                "comment_id": str(comment_id),
                "up_count": up_count,
                "down_count": down_count,
                "user_id": str(current_user.id),
                "my_reaction": my_reaction
            }
        )
    except Exception as e:
        logger.warning(f"Failed to broadcast reaction update: {e}")
    
    logger.info(
        "Comment reaction updated",
        comment_id=str(comment_id),
        user_id=str(current_user.id),
        reaction_type=reaction_data.type,
        up_count=up_count,
        down_count=down_count
    )
    
    return ReactionResponse(
        up_count=up_count,
        down_count=down_count,
        my_reaction=my_reaction
    )


@router.delete("/{comment_id}/reactions", response_model=ReactionResponse)
async def clear_comment_reaction(
    comment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ReactionResponse:
    """Remove the current user's reaction from a comment.
    
    Args:
        comment_id: The comment ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated reaction counts and null my_reaction
        
    Raises:
        HTTPException: If comment not found
    """
    # Verify comment exists
    comment_result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.is_deleted == False)
    )
    comment = comment_result.scalar_one_or_none()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Get existing reaction
    existing_reaction_result = await db.execute(
        select(CommentReaction).where(
            CommentReaction.comment_id == comment_id,
            CommentReaction.user_id == current_user.id
        )
    )
    existing_reaction = existing_reaction_result.scalar_one_or_none()
    
    if existing_reaction:
        await db.delete(existing_reaction)
        await db.commit()
    
    # Get updated counts
    up_count, down_count = await get_comment_reaction_counts(comment_id, db)
    
    # Broadcast to WebSocket
    try:
        await manager.broadcast_to_room(
            f"proposal:{comment.poll_id}",
            {
                "type": "comment_reaction",
                "comment_id": str(comment_id),
                "up_count": up_count,
                "down_count": down_count,
                "user_id": str(current_user.id),
                "my_reaction": None
            }
        )
    except Exception as e:
        logger.warning(f"Failed to broadcast reaction removal: {e}")
    
    logger.info(
        "Comment reaction removed",
        comment_id=str(comment_id),
        user_id=str(current_user.id),
        up_count=up_count,
        down_count=down_count
    )
    
    return ReactionResponse(
        up_count=up_count,
        down_count=down_count,
        my_reaction=None
    )


@router.get("/{comment_id}/reactions/summary", response_model=ReactionSummary)
async def get_comment_reaction_summary(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ReactionSummary:
    """Get reaction summary for a comment.
    
    Args:
        comment_id: The comment ID
        db: Database session
        
    Returns:
        Reaction counts
        
    Raises:
        HTTPException: If comment not found
    """
    # Verify comment exists
    comment_result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.is_deleted == False)
    )
    comment = comment_result.scalar_one_or_none()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Get counts
    up_count, down_count = await get_comment_reaction_counts(comment_id, db)
    
    return ReactionSummary(
        up_count=up_count,
        down_count=down_count
    )
