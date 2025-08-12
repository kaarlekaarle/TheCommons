from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class CommentUser(BaseModel):
    """Schema for user information in comments."""
    
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")


class CommentIn(BaseModel):
    """Schema for creating a new comment."""
    
    body: str = Field(..., min_length=1, max_length=2000, description="Comment body (1-2000 characters)")
    
    @validator('body')
    def validate_body(cls, v):
        """Validate and sanitize comment body."""
        # Trim whitespace
        v = v.strip()
        if not v:
            raise ValueError('Comment body cannot be empty')
        if len(v) > 2000:
            raise ValueError('Comment body cannot exceed 2000 characters')
        # Return sanitized text (plain text only)
        return v


class CommentOut(BaseModel):
    """Schema for comment output."""
    
    id: str = Field(..., description="Comment ID")
    poll_id: str = Field(..., description="Poll ID")
    user: CommentUser = Field(..., description="User who created the comment")
    body: str = Field(..., description="Comment body")
    created_at: str = Field(..., description="ISO datetime when comment was created")
    up_count: int = Field(default=0, description="Number of up reactions")
    down_count: int = Field(default=0, description="Number of down reactions")
    my_reaction: Optional[Literal['up', 'down']] = Field(default=None, description="Current user's reaction")
    
    class Config:
        from_attributes = True


class CommentList(BaseModel):
    """Schema for paginated comment list."""
    
    comments: list[CommentOut] = Field(..., description="List of comments")
    total: int = Field(..., description="Total number of comments")
    limit: int = Field(..., description="Number of comments per page")
    offset: int = Field(..., description="Offset for pagination")
    has_more: bool = Field(..., description="Whether there are more comments to load")
