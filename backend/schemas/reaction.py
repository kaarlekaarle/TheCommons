"""Comment reaction schemas for The Commons."""
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class ReactionIn(BaseModel):
    """Input schema for creating/updating a reaction."""
    type: Literal['up', 'down']


class ReactionOut(BaseModel):
    """Output schema for a reaction."""
    id: UUID
    comment_id: UUID
    user_id: UUID
    type: Literal['up', 'down']
    created_at: datetime

    class Config:
        from_attributes = True


class ReactionSummary(BaseModel):
    """Summary of reactions for a comment."""
    up_count: int
    down_count: int


class ReactionResponse(BaseModel):
    """Response for reaction operations."""
    up_count: int
    down_count: int
    my_reaction: Optional[Literal['up', 'down']] = None
