from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field




class DelegationBase(BaseModel):
    """Base schema for delegation data."""

    delegatee_id: UUID
    poll_id: Optional[UUID] = None
    start_date: datetime
    end_date: Optional[datetime] = None




class DelegationCreate(DelegationBase):
    """Schema for creating a new delegation."""

    pass




class DelegationUpdate(BaseModel):
    """Schema for updating an existing delegation."""

    end_date: Optional[datetime] = None




class Delegation(DelegationBase):
    """Schema for delegation data as returned by the API."""

    id: UUID
    delegator_id: UUID
    chain_origin_id: Optional[UUID] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)




class DelegationStats(BaseModel):
    """Schema for delegation statistics."""

    top_delegatees: List[dict]
    avg_chain_length: float
    longest_chain: int
    active_delegations: int
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)




class DelegationChainResponse(BaseModel):
    final_delegatee_id: UUID
    chain_length: int
    is_circular: bool = False
    exceeds_max_depth: bool = False
    reason: Optional[str] = None




class DelegationTransparencyResponse(BaseModel):
    """Response model for delegation transparency information."""

    poll_id: UUID
    total_delegations: int
    active_delegations: int
    total_delegators: int
    total_delegatees: int
    delegation_chains: List[DelegationChainResponse]

    model_config = ConfigDict(from_attributes=True)




class DelegationStatsResponse(BaseModel):
    """Response model for delegation statistics."""

    top_delegatees: List[dict] = Field(
        ..., description="List of top delegatees with their delegation counts"
    )
    avg_chain_length: float = Field(
        ..., description="Average length of delegation chains"
    )
    longest_chain: int = Field(
        ..., description="Length of the longest delegation chain"
    )
    active_delegations: int = Field(
        ..., description="Total number of active delegations"
    )




class DelegationListResponse(BaseModel):
    """Response model for a list of delegations."""

    delegations: List[Delegation]

    model_config = ConfigDict(from_attributes=True)
