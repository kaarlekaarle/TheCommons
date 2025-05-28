from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func

from backend.core.types import GUID
from backend.models.base import SQLAlchemyBase




class Vote(SQLAlchemyBase):
    __tablename__ = "votes"

    user_id = Column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )  # type: Optional[GUID]
    poll_id = Column(
        GUID(), ForeignKey("polls.id", ondelete="CASCADE"), nullable=False
    )  # type: Optional[GUID]
    option_id = Column(
        GUID(), ForeignKey("options.id", ondelete="CASCADE"), nullable=False
    )  # type: Optional[GUID]
    weight = Column(Integer, default=1)  # type: Optional[Integer]
    comment = Column(String, nullable=True)  # type: Optional[String]
    ip_address = Column(String, nullable=True)  # type: Optional[String]
    user_agent = Column(String, nullable=True)  # type: Optional[String]
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()
    )  # type: Optional[DateTime]
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now()
    )  # type: Optional[DateTime]
    is_deleted = Column(Boolean, default=False)  # type: Optional[Boolean]
    deleted_at = Column(DateTime(timezone=True))  # type: Optional[DateTime]

    # Relationships
    user = relationship("User", back_populates="votes")  # type: Optional[relationship]
    poll = relationship("Poll", back_populates="votes")  # type: Optional[relationship]
    option = relationship(
        "Option", back_populates="votes"
    )  # type: Optional[relationship]

    async def soft_delete(self, db_session: Session) -> None:
        """Soft delete the vote.

        Args:
            db_session: The database session to use for the operation.
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        # Update option vote count
        if self.option:
            self.option.vote_count = max(0, self.option.vote_count - self.weight)
