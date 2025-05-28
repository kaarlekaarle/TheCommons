from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field




class OptionBase(BaseModel):
    """Base schema for option data."""

    text: str = Field(..., min_length=1, max_length=200)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)




class OptionCreate(OptionBase):
    """Schema for creating a new option."""

    poll_id: UUID




class OptionUpdate(OptionBase):
    """Schema for updating an existing option."""

    pass




class Option(OptionBase):
    """Schema for option data as returned by the API."""

    id: UUID
    poll_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
