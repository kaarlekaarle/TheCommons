from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.types import GUID
from backend.models.base import SQLAlchemyBase


class Delegation(SQLAlchemyBase):
    __tablename__ = "delegations"

    delegator_id = Column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    delegate_id = Column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now()
    )
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))

    # Relationships
    delegator = relationship("User", foreign_keys=[delegator_id], back_populates="delegations_as_delegator")
    delegate = relationship("User", foreign_keys=[delegate_id], back_populates="delegations_as_delegate")

    async def soft_delete(self, db_session) -> None:
        """Soft delete the delegation."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
