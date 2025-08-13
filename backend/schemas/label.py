from datetime import datetime
from typing import Optional, Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator
import re

# Custom UUID field that serializes to string
UUIDString = Annotated[UUID, PlainSerializer(lambda x: str(x), return_type=str)]


class LabelBase(BaseModel):
    """Base schema for label data."""
    name: str = Field(..., min_length=2, max_length=40, description="Human-readable label name")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate label name format."""
        if not v.strip():
            raise ValueError('Label name cannot be empty')
        return v.strip()


class LabelCreate(LabelBase):
    """Schema for creating a new label."""
    pass


class LabelUpdate(BaseModel):
    """Schema for updating a label."""
    name: Optional[str] = Field(None, min_length=2, max_length=40)
    is_active: Optional[bool] = None


class Label(LabelBase):
    """Schema for label data as returned by the API."""
    id: UUIDString
    slug: str = Field(..., description="URL-safe slug for the label")
    is_active: bool = Field(..., description="Whether the label is active")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a label name."""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    
    # Ensure it matches the required pattern
    if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', slug):
        # Fallback: use a simple alphanumeric version
        slug = re.sub(r'[^a-z0-9]', '', name.lower())
        if not slug:
            slug = 'label'
    
    return slug
