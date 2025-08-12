from typing import List, Union
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, union_all, text
from sqlalchemy.ext.asyncio import AsyncSession

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
        # Return a simple test response
        activity_items = [
            {
                "type": "proposal",
                "id": "test-id",
                "user": {
                    "id": "test-user-id",
                    "username": "admin"
                },
                "timestamp": "2025-08-11T19:46:57.836969Z",
                "details": "created a proposal: Test Proposal"
            }
        ]
        
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
