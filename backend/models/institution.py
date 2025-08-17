"""Institution model for institution-based delegations."""

from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.types import GUID
from backend.models.base import SQLAlchemyBase


class InstitutionKind(str, Enum):
    """Types of institutions that can be delegated to."""

    NGO = "ngo"  # Non-governmental organization
    COOP = "coop"  # Cooperative
    PARTY = "party"  # Political party
    CIVIC = "civic"  # Civic organization
    OTHER = "other"  # Other institution type


class Institution(SQLAlchemyBase):
    """Institution model representing organizations that can receive delegations."""

    __tablename__ = "institutions"

    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    kind = Column(String(20), nullable=False, default=InstitutionKind.OTHER)
    url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    delegations = relationship("Delegation", back_populates="institution")

    def __repr__(self) -> str:
        """String representation of the institution."""
        return (
            f"<Institution(slug='{self.slug}', name='{self.name}', kind='{self.kind}')>"
        )
