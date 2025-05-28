from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.future import select
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.core.types import GUID
from backend.models.base import SQLAlchemyBase




class Option(SQLAlchemyBase):
    __tablename__ = "options"

    text = Column(String, nullable=False)  # type: Any
    description = Column(String, nullable=True)  # type: Any
    poll_id = Column(
        GUID(), ForeignKey("polls.id", ondelete="CASCADE"), nullable=False
    )  # type: Any
    order = Column(Integer, default=0)  # type: Any
    is_correct = Column(Boolean, default=False)  # type: Any
    vote_count = Column(Integer, default=0)  # type: Any
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # type: Any
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # type: Any
    is_deleted = Column(Boolean, default=False)  # type: Any
    deleted_at = Column(DateTime(timezone=True))  # type: Any

    # Relationships
    poll = relationship("Poll", back_populates="options")  # type: Any
    votes = relationship(
        "Vote", back_populates="option", cascade="all, delete-orphan"
    )  # type: Any

    async def soft_delete(self, db_session):
        """Soft delete the option and all related votes."""
        from backend.models.vote import Vote  # Import here to avoid circular dependency

        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        # Soft delete related votes
        result = await db_session.execute(
            select(Vote).where(Vote.option_id == self.id, Vote.is_deleted == False)
        )
        votes = result.scalars().all()
        for vote in votes:
            await vote.soft_delete(db_session)

    def is_active(self) -> bool:
        """Check if option is active."""
        return self.is_deleted is False
