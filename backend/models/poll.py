from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.future import select
from sqlalchemy.orm import Session, relationship

from backend.core.types import GUID
from backend.models.base import SQLAlchemyBase




class PollStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"




class PollVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"




class Poll(SQLAlchemyBase):
    """Poll model."""

    __tablename__ = "polls"

    title = Column(String, nullable=False)  # type: Any
    description = Column(String, nullable=True)  # type: Any
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)  # type: Any
    status = Column(
        SQLEnum(PollStatus), default=PollStatus.DRAFT, nullable=False
    )  # type: Any
    visibility = Column(
        SQLEnum(PollVisibility), default=PollVisibility.PUBLIC, nullable=False
    )  # type: Any
    start_date = Column(DateTime(timezone=True), nullable=True)  # type: Any
    end_date = Column(DateTime(timezone=True), nullable=True)  # type: Any
    allow_delegation = Column(Boolean, default=True)  # type: Any
    require_authentication = Column(Boolean, default=True)  # type: Any
    max_votes_per_user = Column(Integer, default=1)  # type: Any

    # Relationships
    user = relationship("User", back_populates="polls")  # type: Any
    options = relationship(
        "Option", back_populates="poll", cascade="all, delete-orphan"
    )  # type: Any
    votes = relationship(
        "Vote", back_populates="poll", cascade="all, delete-orphan"
    )  # type: Any
    comments = relationship(
        "Comment", back_populates="poll", cascade="all, delete-orphan"
    )  # type: Any

    async def soft_delete(self, db_session: Session) -> None:
        """Soft delete the poll and all related data.

        This method performs a soft delete of the poll and all its related data,
        including options, votes, and activity logs.

        Args:
            db_session: The database session to use for the operation.
        """
        from backend.models.activity_log import (
            ActivityLog,  # Import here to avoid circular dependency
        )
        from backend.models.option import (
            Option,  # Import here to avoid circular dependency
        )
        from backend.models.vote import Vote  # Import here to avoid circular dependency

        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        # Soft delete related options
        result = await db_session.execute(
            select(Option).where(Option.poll_id == self.id, Option.is_deleted == False)
        )
        options = result.scalars().all()
        for option in options:
            await option.soft_delete(db_session)
        # Soft delete related votes
        result = await db_session.execute(
            select(Vote).where(Vote.poll_id == self.id, Vote.is_deleted == False)
        )
        votes = result.scalars().all()
        for vote in votes:
            await vote.soft_delete(db_session)
        # Soft delete related activity logs
        result = await db_session.execute(
            select(ActivityLog).where(
                ActivityLog.reference_id == self.id, ActivityLog.is_deleted == False
            )
        )
        activities = result.scalars().all()
        for activity in activities:
            await activity.soft_delete(db_session)
        # Commit all changes
        await db_session.commit()

    def is_active(self) -> bool:
        """Check if poll is active."""
        return self.is_deleted is False and self.end_date is None or self.end_date > datetime.utcnow()

    def is_closed(self) -> bool:
        """Check if poll is closed."""
        return self.is_deleted is False and self.end_date is not None and self.end_date <= datetime.utcnow()
