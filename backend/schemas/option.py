from datetime import datetime
from typing import Optional, Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

# Custom UUID field that serializes to string
UUIDString = Annotated[UUID, PlainSerializer(lambda x: str(x), return_type=str)]




class OptionBase(BaseModel):
    """Base schema for option data."""

    text: str = Field(..., min_length=1, max_length=200)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)




class OptionCreate(OptionBase):
    """Schema for creating a new option."""

    poll_id: UUIDString




class OptionUpdate(OptionBase):
    """Schema for updating an existing option."""

    pass




class Option(OptionBase):
    """Schema for option data as returned by the API."""

    id: UUIDString
    poll_id: UUIDString
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
