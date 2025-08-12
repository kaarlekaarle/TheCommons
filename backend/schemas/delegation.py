from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DelegationBase(BaseModel):
    """Base schema for delegation data."""
    delegate_id: UUID = Field(..., description="ID of the user being delegated to")


class DelegationCreate(DelegationBase):
    """Schema for creating a new delegation."""
    pass


class DelegationUpdate(BaseModel):
    """Schema for updating a delegation."""
    delegate_id: Optional[UUID] = None


class Delegation(DelegationBase):
    """Schema for delegation data as returned by the API."""
    id: UUID
    delegator_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DelegationResponse(BaseModel):
    """Schema for delegation response."""
    id: UUID
    delegator_id: UUID
    delegate_id: UUID
    delegate_username: str
    delegate_email: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DelegationInfo(BaseModel):
    """Schema for delegation info."""
    has_delegate: bool
    delegate_id: Optional[UUID] = None
    delegate_username: Optional[str] = None
    delegate_email: Optional[str] = None
    created_at: Optional[datetime] = None
