from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.comment import Comment
from backend.models.poll import Poll
from backend.models.user import User
from backend.schemas.comment import CommentIn, CommentOut, CommentList, CommentUser
from backend.core.auth import get_current_active_user
from backend.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["comments"])


@router.get("/{poll_id}/comments", response_model=CommentList)
async def list_comments(
    poll_id: UUID,
    limit: int = Query(20, ge=1, le=100, description="Number of comments to return"),
    offset: int = Query(0, ge=0, description="Number of comments to skip"),
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
            comment_output = CommentOut(
                id=str(comment.id),
                poll_id=str(comment.poll_id),
                user=CommentUser(
                    id=str(comment.user.id),
                    username=comment.user.username
                ),
                body=comment.body,
                created_at=comment.created_at.isoformat() + "Z"
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
        if comment.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments"
            )
        
        # Soft delete
        comment.is_deleted = True
        await db.commit()
        
        logger.info(
            "Comment deleted successfully",
            extra={"comment_id": str(comment_id)}
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
