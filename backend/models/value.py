"""Value entity model for values-as-delegates functionality.

This model supports delegation to abstract values/principles rather than just people.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.types import GUID
from backend.models.base import SQLAlchemyBase


class Value(SQLAlchemyBase):
    """Model for abstract values/principles that can be delegated to."""
    
    __tablename__ = "values"

    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    slug = Column(String, nullable=False, unique=True, index=True)
    
    # Constitutional fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))

    # Relationships
    delegations = relationship("Delegation", back_populates="value")

    async def soft_delete(self, db_session) -> None:
        """Soft delete the value."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
