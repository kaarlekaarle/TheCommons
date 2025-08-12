from typing import Optional, List
from pydantic import BaseModel, Field


class PrincipleItem(BaseModel):
    """A Level A principle/baseline policy item."""
    id: str = Field(..., description="Unique identifier for the principle")
    title: str = Field(..., description="Short, descriptive title")
    description: str = Field(..., description="Detailed description of the principle")
    tags: Optional[List[str]] = Field(default=None, description="Categories or tags")
    source: Optional[str] = Field(default=None, description="Source or origin of the principle")


class ActionItem(BaseModel):
    """A Level B action/specific proposal item."""
    id: str = Field(..., description="Unique identifier for the action")
    title: str = Field(..., description="Short, descriptive title")
    description: str = Field(..., description="Detailed description of the action")
    scope: Optional[str] = Field(default=None, description="Scope: city, district, org, etc.")
    tags: Optional[List[str]] = Field(default=None, description="Categories or tags")
    source: Optional[str] = Field(default=None, description="Source or origin of the action")


class StoryItem(BaseModel):
    """A case study or success story for landing/dashboard."""
    id: str = Field(..., description="Unique identifier for the story")
    title: str = Field(..., description="Short, descriptive title")
    summary: str = Field(..., description="Brief summary of the story")
    impact: Optional[str] = Field(default=None, description="Measurable impact or outcomes")
    link: Optional[str] = Field(default=None, description="Optional link to more details")


class ContentResponse(BaseModel):
    """Generic response wrapper for content lists."""
    items: List[PrincipleItem | ActionItem | StoryItem]
    count: int
    source: str = Field(..., description="Source of the content: 'demo' or 'file'")
