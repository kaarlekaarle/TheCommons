from datetime import datetime
from typing import Any, List
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.types import GUID
from backend.models.base import SQLAlchemyBase


class Label(SQLAlchemyBase):
    """Label model for topic categorization."""

    __tablename__ = "labels"

    name = Column(String(40), nullable=False)  # type: Any
    slug = Column(String(40), nullable=False, unique=True, index=True)  # type: Any
    is_active = Column(Boolean, default=True, nullable=False)  # type: Any
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )  # type: Any
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )  # type: Any

    # Relationships
    polls = relationship(
        "Poll",
        secondary="poll_labels",
        back_populates="labels",
        lazy="selectin"
    )  # type: Any
    delegations = relationship(
        "Delegation", 
        back_populates="label",
        cascade="all, delete-orphan"
    )  # type: Any

    __table_args__ = (
        UniqueConstraint('name', name='idx_label_name_unique'),
        UniqueConstraint('slug', name='idx_label_slug_unique'),
    )

    async def soft_delete(self, db_session) -> None:
        """Soft delete the label by deactivating it."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
