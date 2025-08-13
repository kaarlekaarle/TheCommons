from typing import List, Union
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, union_all, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
# from backend.core.logging_config import get_logger
from backend.models.poll import Poll
from backend.models.vote import Vote
from backend.models.delegation import Delegation
from backend.models.user import User
from backend.schemas.activity import ActivityItem, ActivityUser

# logger = get_logger(__name__)
router = APIRouter(tags=["activity"])


@router.get("/")
async def get_activity_feed(
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest activity feed.
    
    Returns the most recent proposals, votes, and delegations in chronological order.
    
    Args:
        limit: Maximum number of items to return (1-100)
        db: Database session
        
    Returns:
        List of activity items ordered by timestamp (newest first)
    """
    # logger.info("Fetching activity feed", extra={"limit": limit})
    
    try:
        # Get recent polls with user information and labels
        query = select(Poll, User).join(User, Poll.created_by == User.id).options(selectinload(Poll.labels)).order_by(Poll.created_at.desc()).limit(limit)
        result = await db.execute(query)
        polls_with_users = result.fetchall()
        
        activity_items = []
        for poll, user in polls_with_users:
            # Create activity message based on decision type
            if poll.decision_type == "level_a" and poll.direction_choice:
                details = f"created a baseline policy: {poll.title} (direction: {poll.direction_choice})"
            else:
                details = f"created a proposal: {poll.title}"
            
            activity_item = {
                "type": "proposal",
                "id": str(poll.id),
                "user": {
                    "id": str(user.id),
                    "username": user.username
                },
                "timestamp": poll.created_at.isoformat(),
                "details": details,
                "decision_type": poll.decision_type,
                "direction_choice": poll.direction_choice
            }
            
            # Add labels if they exist
            if poll.labels:
                activity_item["labels"] = [{"name": label.name, "slug": label.slug} for label in poll.labels]
            
            activity_items.append(activity_item)
        
        # logger.info(
        #     "Activity feed retrieved successfully",
        #     extra={"item_count": len(activity_items)}
        # )
        
        return activity_items
        
    except Exception as e:
        # logger.error(
        #     "Failed to fetch activity feed",
        #     extra={"error": str(e)},
        #     exc_info=True
        # )
        raise
