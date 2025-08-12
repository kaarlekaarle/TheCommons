from datetime import datetime
from typing import Optional, Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

# Custom UUID field that serializes to string
UUIDString = Annotated[UUID, PlainSerializer(lambda x: str(x), return_type=str)]




class VoteBase(BaseModel):
    """Base schema for vote data."""

    poll_id: UUIDString
    option_id: UUIDString




class VoteCreate(VoteBase):
    """Schema for creating a new vote."""

    pass




class VoteUpdate(BaseModel):
    """Schema for updating an existing vote."""

    option_id: Optional[UUIDString] = None




class Vote(VoteBase):
    """Schema for vote data as returned by the API."""

    id: UUIDString
    user_id: UUIDString
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)




class VoteResponse(BaseModel):
    # ... fields ...
    model_config = ConfigDict(from_attributes=True)
