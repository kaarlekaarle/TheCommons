"""Telemetry endpoints for tracking user interactions."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import get_current_active_user
from backend.database import get_db
from backend.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


class ComposerOpenRequest(BaseModel):
    mode: str


class DelegationCreatedRequest(BaseModel):
    mode: str


@router.post("/composer-open")
async def track_composer_open(
    request: ComposerOpenRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Track when a user opens the composer with a specific mode.
    
    Args:
        request: The composer open request with mode
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        dict: Success response
    """
    try:
        logger.info(
            "Composer opened",
            extra={
                "user_id": str(current_user.id),
                "mode": request.mode,
            },
        )
        
        # For now, just log the event
        # In the future, this could be stored in a telemetry table
        return {"status": "success", "message": "Composer open tracked"}
        
    except Exception as e:
        logger.error(
            "Failed to track composer open",
            extra={"error": str(e), "user_id": str(current_user.id)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to track composer open")


@router.post("/delegation-created")
async def track_delegation_created(
    request: DelegationCreatedRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Track when a user creates a delegation with a specific mode.
    
    Args:
        request: The delegation created request with mode
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        dict: Success response
    """
    try:
        logger.info(
            "Delegation created",
            extra={
                "user_id": str(current_user.id),
                "mode": request.mode,
            },
        )
        
        # For now, just log the event
        # In the future, this could be stored in a telemetry table
        return {"status": "success", "message": "Delegation created tracked"}
        
    except Exception as e:
        logger.error(
            "Failed to track delegation created",
            extra={"error": str(e), "user_id": str(current_user.id)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to track delegation created")
