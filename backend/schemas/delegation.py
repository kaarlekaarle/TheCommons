from datetime import datetime
from typing import Optional, Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

# Custom UUID field that serializes to string
UUIDString = Annotated[UUID, PlainSerializer(lambda x: str(x), return_type=str)]


class DelegationBase(BaseModel):
    """Base schema for delegation data."""
    delegate_id: UUIDString = Field(..., description="ID of the user being delegated to")


class DelegationCreate(DelegationBase):
    """Schema for creating a new delegation."""
    pass


class DelegationUpdate(BaseModel):
    """Schema for updating a delegation."""
    delegate_id: Optional[UUIDString] = None


class Delegation(DelegationBase):
    """Schema for delegation data as returned by the API."""
    id: UUIDString
    delegator_id: UUIDString
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DelegationResponse(BaseModel):
    """Schema for delegation response."""
    id: UUIDString
    delegator_id: UUIDString
    delegate_id: UUIDString
    delegate_username: str
    delegate_email: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DelegationInfo(BaseModel):
    """Schema for delegation info."""
    has_delegate: bool
    delegate_id: Optional[UUIDString] = None
    delegate_username: Optional[str] = None
    delegate_email: Optional[str] = None
    created_at: Optional[datetime] = None
