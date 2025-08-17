"""Field model for field-based delegations."""

from sqlalchemy import Column, DateTime, String, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.types import GUID
from backend.models.base import SQLAlchemyBase


class Field(SQLAlchemyBase):
    """Field model representing domains of expertise or interest."""

    __tablename__ = "fields"

    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, server_default="true")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relationships
    delegations = relationship("Delegation", back_populates="field")

    def __repr__(self) -> str:
        """String representation of the field."""
        return f"<Field(slug='{self.slug}', name='{self.name}')>"
