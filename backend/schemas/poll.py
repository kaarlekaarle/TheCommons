from datetime import datetime
from typing import List, Optional, Literal, Annotated, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator, PlainSerializer, field_validator
from backend.models.option import Option
from backend.models.poll import DecisionType
from backend.schemas.label import Label

# Custom UUID field that serializes to string
UUIDString = Annotated[UUID, PlainSerializer(lambda x: str(x), return_type=str)]

# Custom DecisionType field that serializes to string
DecisionTypeString = Annotated[DecisionType, PlainSerializer(lambda x: x.value, return_type=str)]


class PollSummary(BaseModel):
    """Schema for poll summary data used in label overview."""
    id: str = Field(..., description="Poll ID")
    title: str = Field(..., description="Poll title")
    decision_type: str = Field(..., description="Decision type (level_a or level_b)")
    created_at: str = Field(..., description="ISO datetime when poll was created")
    labels: List[dict] = Field(..., description="List of labels with name and slug")

    model_config = ConfigDict(from_attributes=True)


class PollBase(BaseModel):
    """Base schema for poll data.
    
    The two-level decision model supports two types of proposals:
    - Level A (Baseline Policy): High-level, slow-changing principles that are rarely updated
    - Level B (Poll): Quick action on specific issues with Yes/No/Abstain voting
    """

    title: str = Field(..., min_length=1, max_length=200, description="Short, clear title for the proposal")
    description: Optional[str] = Field(None, max_length=1000, description="Detailed explanation of the proposal")
    decision_type: Literal["level_a", "level_b"] = Field(
        "level_b", 
        description="Decision type: 'level_a' for baseline policy (requires direction_choice), 'level_b' for poll (ignores direction_choice)"
    )
    direction_choice: Optional[str] = Field(
        None, 
        max_length=200, 
        description="Required for Level A decisions. Specifies the baseline direction (e.g., 'Environmental Policy', 'Transportation Safety')"
    )
    labels: List[Union[str, UUIDString]] = Field(
        default_factory=list,
        max_length=5,
        description="List of label slugs or IDs (max 5 labels per poll)"
    )

    @field_validator('labels')
    @classmethod
    def validate_labels(cls, v: List[Union[str, UUIDString]]) -> List[Union[str, UUIDString]]:
        """Validate labels list."""
        if len(v) > 5:
            raise ValueError('Maximum 5 labels allowed per poll')
        return v

    @model_validator(mode='after')
    def validate_direction_choice(self):
        if self.decision_type == 'level_a' and not self.direction_choice:
            raise ValueError('direction_choice is required when decision_type is level_a')
        return self




class PollCreate(PollBase):
    """Schema for creating a new poll."""

    pass




class PollUpdate(PollBase):
    """Schema for updating an existing poll."""

    pass




class VoteStatus(BaseModel):
    """Schema for vote status information."""

    status: str = Field(
        ..., description="Current vote status: 'delegated', 'voted', or 'none'"
    )
    resolved_vote_path: List[UUIDString] = Field(
        default_factory=list, description="Path of delegation chain"
    )
    final_delegatee_id: Optional[UUIDString] = Field(
        None, description="ID of the final delegatee in the chain"
    )

    model_config = ConfigDict(from_attributes=True)




class PollResult(BaseModel):
    """Schema for poll result data."""

    option_id: UUIDString = Field(..., description="ID of the option")
    text: str = Field(..., description="Text of the option")
    direct_votes: int = Field(..., description="Number of direct votes")
    delegated_votes: int = Field(..., description="Number of delegated votes")
    total_votes: int = Field(..., description="Total votes (direct + delegated)")

    model_config = ConfigDict(from_attributes=True)




class Poll(PollBase):
    """Schema for poll data as returned by the API."""

    id: UUIDString
    created_by: UUIDString
    created_at: datetime
    updated_at: Optional[datetime] = None
    decision_type: DecisionTypeString
    labels: List[Label] = Field(
        default_factory=list,
        description="List of labels associated with this poll"
    )
    your_vote_status: Optional[VoteStatus] = Field(
        None, description="Vote status for the current user"
    )

    model_config = ConfigDict(from_attributes=True)




class PollWithOptions(Poll):
    """Schema for poll data with options."""

    options: List["Option"] = []

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)
