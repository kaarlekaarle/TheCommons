"""Unified target view for searching across people, fields, and institutions."""

from sqlalchemy import Column, String, Text, Boolean, Float
from sqlalchemy.orm import Query

from backend.core.types import GUID
from backend.models.base import SQLAlchemyBase


class UnifiedTarget(SQLAlchemyBase):
    """Unified view for searching across people, fields, and institutions."""

    __tablename__ = "unified_targets"

    # Common fields
    target_type = Column(String(20), nullable=False)  # 'user', 'field', 'institution'
    target_id = Column(GUID(), nullable=False)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    
    # Metadata for ranking and filtering
    tags = Column(Text, nullable=True)  # JSON array of tags
    popularity_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    
    # Constitutional transparency fields
    created_at = Column(String(30), nullable=True)  # ISO timestamp
    updated_at = Column(String(30), nullable=True)  # ISO timestamp

    def __repr__(self) -> str:
        """String representation of the unified target."""
        return f"<UnifiedTarget(type='{self.target_type}', id='{self.target_id}', name='{self.name}')>"

    @classmethod
    def create_from_user(cls, user):
        """Create unified target from User model."""
        return cls(
            target_type="user",
            target_id=user.id,
            name=user.display_name or user.username,
            slug=user.username,
            description=user.bio,
            tags=user.tags if hasattr(user, 'tags') else None,
            popularity_score=getattr(user, 'popularity_score', 0.0),
            is_active=not user.is_deleted if hasattr(user, 'is_deleted') else True,
            created_at=user.created_at.isoformat() if user.created_at else None,
            updated_at=user.updated_at.isoformat() if user.updated_at else None
        )

    @classmethod
    def create_from_field(cls, field):
        """Create unified target from Field model."""
        return cls(
            target_type="field",
            target_id=field.id,
            name=field.name,
            slug=field.slug,
            description=field.description,
            tags=None,  # Fields don't have tags yet
            popularity_score=0.0,  # TODO: Calculate based on delegation count
            is_active=field.is_active,
            created_at=field.created_at.isoformat() if field.created_at else None,
            updated_at=field.updated_at.isoformat() if field.updated_at else None
        )

    @classmethod
    def create_from_institution(cls, institution):
        """Create unified target from Institution model."""
        return cls(
            target_type="institution",
            target_id=institution.id,
            name=institution.name,
            slug=institution.slug,
            description=institution.description,
            tags=[institution.kind],  # Use institution kind as tag
            popularity_score=0.0,  # TODO: Calculate based on delegation count
            is_active=institution.is_active,
            created_at=institution.created_at.isoformat() if institution.created_at else None,
            updated_at=institution.updated_at.isoformat() if institution.updated_at else None
        )
