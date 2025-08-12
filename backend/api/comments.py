from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.comment import Comment
from backend.models.comment_reaction import CommentReaction, ReactionType
from backend.models.poll import Poll
from backend.models.user import User
from backend.schemas.comment import CommentIn, CommentOut, CommentList, CommentUser
from backend.core.auth import get_current_active_user
from backend.core.logging_config import get_logger
from backend.core.audit_mw import audit_event
from backend.core.admin_audit import log_admin_action

logger = get_logger(__name__)
router = APIRouter(tags=["comments"])


async def get_comment_reaction_data(comment_id: UUID, user_id: Optional[UUID], db: AsyncSession) -> tuple[int, int, Optional[str]]:
    """Get reaction data for a comment."""
    # Get counts
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
    
    # Get user's reaction if user_id provided
    my_reaction = None
    if user_id:
        reaction_result = await db.execute(
            select(CommentReaction).where(
                CommentReaction.comment_id == comment_id,
                CommentReaction.user_id == user_id
            )
        )
        reaction = reaction_result.scalar_one_or_none()
        if reaction:
            my_reaction = reaction.type.value
    
    return up_count, down_count, my_reaction


@router.get("/{poll_id}/comments", response_model=CommentList)
async def list_comments(
    poll_id: UUID,
    limit: int = Query(20, ge=1, le=100, description="Number of comments to return"),
    offset: int = Query(0, ge=0, description="Number of comments to skip"),
    current_user: Optional[User] = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CommentList:
    """Get comments for a specific poll.
    
    Args:
        poll_id: The poll ID
        limit: Maximum number of comments to return (1-100)
        offset: Number of comments to skip for pagination
        db: Database session
        
    Returns:
        Paginated list of comments ordered by creation time (newest first)
    """
    logger.info("Fetching comments", extra={"poll_id": str(poll_id), "limit": limit, "offset": offset})
    
    try:
        # Check if poll exists and is not deleted
        result = await db.execute(
            select(Poll).where(Poll.id == poll_id, Poll.is_deleted == False)
        )
        poll = result.scalar_one_or_none()
        if not poll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Poll not found"
            )
        
        # Get total count
        count_result = await db.execute(
            select(func.count(Comment.id)).where(
                Comment.poll_id == poll_id,
                Comment.is_deleted == False
            )
        )
        total = count_result.scalar()
        
        # Get comments with pagination
        result = await db.execute(
            select(Comment)
            .where(Comment.poll_id == poll_id, Comment.is_deleted == False)
            .order_by(Comment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        comments = result.scalars().all()
        
        # Convert to output format
        comment_outputs = []
        for comment in comments:
            # Get reaction data
            up_count, down_count, my_reaction = await get_comment_reaction_data(
                comment.id, 
                current_user.id if current_user else None, 
                db
            )
            
            comment_output = CommentOut(
                id=str(comment.id),
                poll_id=str(comment.poll_id),
                user=CommentUser(
                    id=str(comment.user.id),
                    username=comment.user.username
                ),
                body=comment.body,
                created_at=comment.created_at.isoformat() + "Z",
                up_count=up_count,
                down_count=down_count,
                my_reaction=my_reaction
            )
            comment_outputs.append(comment_output)
        
        has_more = offset + limit < total
        
        logger.info(
            "Comments retrieved successfully",
            extra={"poll_id": str(poll_id), "count": len(comment_outputs), "total": total}
        )
        
        return CommentList(
            comments=comment_outputs,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch comments",
            extra={"poll_id": str(poll_id), "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch comments"
        )


@router.post("/{poll_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(
    request: Request,
    poll_id: UUID,
    comment_in: CommentIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CommentOut:
    """Create a new comment on a poll.
    
    Args:
        poll_id: The poll ID
        comment_in: Comment data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created comment
    """
    logger.info("Creating comment", extra={"poll_id": str(poll_id), "user_id": str(current_user.id)})
    
    try:
        # Check if poll exists and is not deleted
        result = await db.execute(
            select(Poll).where(Poll.id == poll_id, Poll.is_deleted == False)
        )
        poll = result.scalar_one_or_none()
        if not poll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Poll not found"
            )
        
        # Create comment
        comment = Comment(
            poll_id=poll_id,
            user_id=current_user.id,
            body=comment_in.body
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        
        # Convert to output format
        comment_output = CommentOut(
            id=str(comment.id),
            poll_id=str(comment.poll_id),
            user=CommentUser(
                id=str(current_user.id),
                username=current_user.username
            ),
            body=comment.body,
            created_at=comment.created_at.isoformat() + "Z"
        )
        
        # Broadcast comment update
        try:
            from backend.core.websocket import manager
            await manager.broadcast_comment_update(str(poll_id), {
                "id": str(comment.id),
                "poll_id": str(comment.poll_id),
                "user": {
                    "id": str(current_user.id),
                    "username": current_user.username
                },
                "body": comment.body,
                "created_at": comment.created_at.isoformat() + "Z"
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast comment creation", extra={"error": str(e)})
        
        logger.info(
            "Comment created successfully",
            extra={"comment_id": str(comment.id), "poll_id": str(poll_id)}
        )
        
        # Audit the comment creation
        audit_event(
            "comment_created",
            {
                "comment_id": str(comment.id),
                "poll_id": str(comment.poll_id),
                "body": comment.body[:100] + "..." if len(comment.body) > 100 else comment.body,
            },
            request
        )
        
        return comment_output
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create comment",
            extra={"poll_id": str(poll_id), "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create comment"
        )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    request: Request,
    comment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a comment (soft delete).
    
    Only the comment author or an admin can delete a comment.
    
    Args:
        comment_id: The comment ID
        current_user: Current authenticated user
        db: Database session
    """
    logger.info("Deleting comment", extra={"comment_id": str(comment_id), "user_id": str(current_user.id)})
    
    try:
        # Get comment
        result = await db.execute(
            select(Comment).where(Comment.id == comment_id, Comment.is_deleted == False)
        )
        comment = result.scalar_one_or_none()
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Check permissions (author or admin)
        is_admin_delete = comment.user_id != current_user.id and current_user.is_superuser
        
        if comment.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments"
            )
        
        # Log admin action if admin is deleting someone else's comment
        if is_admin_delete:
            log_admin_action(
                action="delete_comment",
                target_resource="comment",
                target_id=str(comment_id),
                details={
                    "comment_author_id": str(comment.user_id),
                    "comment_author_username": comment.user.username,
                    "poll_id": str(comment.poll_id)
                },
                user=current_user
            )
        
        # Soft delete
        comment.is_deleted = True
        await db.commit()
        
        logger.info(
            "Comment deleted successfully",
            extra={"comment_id": str(comment_id)}
        )
        
        # Audit the comment deletion
        audit_event(
            "comment_deleted",
            {
                "comment_id": str(comment_id),
                "poll_id": str(comment.poll_id),
                "is_admin_delete": is_admin_delete,
            },
            request
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete comment",
            extra={"comment_id": str(comment_id), "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete comment"
        )
