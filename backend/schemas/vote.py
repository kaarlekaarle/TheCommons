from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field




class VoteBase(BaseModel):
    """Base schema for vote data."""

    poll_id: UUID
    option_id: UUID




class VoteCreate(VoteBase):
    """Schema for creating a new vote."""

    pass




class VoteUpdate(BaseModel):
    """Schema for updating an existing vote."""

    option_id: Optional[UUID] = None




class Vote(VoteBase):
    """Schema for vote data as returned by the API."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)




class VoteResponse(BaseModel):
    # ... fields ...
    model_config = ConfigDict(from_attributes=True)
