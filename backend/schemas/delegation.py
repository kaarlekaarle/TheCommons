from datetime import datetime
from typing import Optional, Annotated, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

# Custom UUID field that serializes to string
UUIDString = Annotated[UUID, PlainSerializer(lambda x: str(x), return_type=str)]


class DelegationBase(BaseModel):
    """Base schema for delegation data."""
    delegatee_id: UUIDString = Field(..., description="ID of the user being delegated to")
    label_slug: Optional[str] = Field(None, description="Label slug for label-specific delegation (mutually exclusive with global)")


class DelegationCreate(DelegationBase):
    """Schema for creating a new delegation."""
    pass


class DelegationUpdate(BaseModel):
    """Schema for updating a delegation."""
    delegatee_id: Optional[UUIDString] = None


class Delegation(DelegationBase):
    """Schema for delegation data as returned by the API."""
    id: UUIDString
    delegator_id: UUIDString
    label_id: Optional[UUIDString] = Field(None, description="ID of the label for label-specific delegation")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DelegationResponse(BaseModel):
    """Schema for delegation response."""
    id: UUIDString
    delegator_id: UUIDString
    delegatee_id: UUIDString
    delegatee_username: str
    delegatee_email: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DelegationInfo(BaseModel):
    """Schema for delegation info."""
    has_delegatee: bool
    delegatee_id: Optional[UUIDString] = None
    delegatee_username: Optional[str] = None
    delegatee_email: Optional[str] = None
    created_at: Optional[datetime] = None


class DelegationSummary(BaseModel):
    """Schema for delegation summary including global and per-label delegations."""
    global_delegate: Optional[DelegationInfo] = None
    per_label: List[dict] = Field(
        default_factory=list,
        description="List of label-specific delegations with label and delegate info"
    )

    model_config = ConfigDict(from_attributes=True)
