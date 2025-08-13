from datetime import datetime
from typing import Literal, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


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
    decision_type: Optional[str] = Field(None, description="Decision type for proposals")
    direction_choice: Optional[str] = Field(None, description="Direction choice for level_a proposals")
    labels: Optional[List[dict]] = Field(None, description="Labels associated with the poll")

    model_config = ConfigDict(from_attributes=True)
