from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ActivityUser(BaseModel):
    """Schema for user information in activity items."""
    
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")


class ActivityItem(BaseModel):
    """Schema for a single activity feed item."""
    
    type: Literal["proposal", "vote", "delegation"] = Field(
        ..., description="Type of activity"
    )
    id: str = Field(..., description="ID of the related entity")
    user: ActivityUser = Field(..., description="User who performed the action")
    timestamp: str = Field(..., description="ISO datetime when the action occurred")
    details: str = Field(..., description="Human-readable description of the action")
