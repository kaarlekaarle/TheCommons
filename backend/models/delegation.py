from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from backend.core.types import GUID

from .base import SQLAlchemyBase




class Delegation(SQLAlchemyBase):
    __tablename__ = "delegation"
    delegator_id = Column(GUID(), ForeignKey("users.id"), nullable=False)  # type: Any
    delegatee_id = Column(GUID(), ForeignKey("users.id"), nullable=False)  # type: Any
    poll_id = Column(GUID(), ForeignKey("polls.id"), nullable=True)  # type: Any
    revoked_at = Column(DateTime, nullable=True)  # type: Any
    chain_origin_id = Column(GUID(), ForeignKey("users.id"), nullable=True)  # type: Any
    start_date = Column(DateTime, nullable=False)  # type: Any
    end_date = Column(DateTime, nullable=True)  # type: Any
    is_deleted = Column(Boolean, default=False)  # type: Any
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # type: Any

    # Relationships
    poll = relationship("Poll", back_populates="delegations")  # type: Any

    def __repr__(self):
        return (
            f"<Delegation(id={self.id}, "
            f"delegator_id={self.delegator_id}, "
            f"delegatee_id={self.delegatee_id}, "
            f"poll_id={self.poll_id})>"
        )

    def revoke(self):
        if not self.end_date:
            self.end_date = datetime.utcnow()

    @classmethod
    async def get_stats(cls, db_session, poll_id=None):
        from backend.services.delegation import DelegationService

        service = DelegationService(db_session)
        return await service.get_delegation_stats(poll_id)

    async def soft_delete(self, db_session):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
