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
    delegatee_id = Column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    poll_id = Column(
        GUID(), ForeignKey("polls.id", ondelete="CASCADE"), nullable=True
    )
    chain_origin_id = Column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    start_date = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    end_date = Column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at = Column(
        DateTime(timezone=True), nullable=True
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
    delegatee = relationship("User", foreign_keys=[delegatee_id], back_populates="delegations_as_delegatee")
    poll = relationship("Poll", back_populates="delegations")
    chain_origin = relationship("User", foreign_keys=[chain_origin_id])

    async def soft_delete(self, db_session) -> None:
        """Soft delete the delegation."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
