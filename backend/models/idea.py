"""Idea entity model for idea-based delegation functionality.

This model supports delegation to specific ideas/proposals rather than just people.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.types import GUID
from backend.models.base import SQLAlchemyBase


class Idea(SQLAlchemyBase):
    """Model for ideas/proposals that can be delegated to."""
    
    __tablename__ = "ideas"

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String, nullable=False, unique=True, index=True)
    
    # Constitutional fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))

    # Relationships
    delegations = relationship("Delegation", back_populates="idea")

    async def soft_delete(self, db_session) -> None:
        """Soft delete the idea."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
