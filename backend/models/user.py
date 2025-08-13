import uuid
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.future import select
from sqlalchemy.orm import Session, relationship
from sqlalchemy.sql import func

from backend.models.base import SQLAlchemyBase




class User(SQLAlchemyBase):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=False)  # type: Any
    username = Column(String, unique=True, index=True, nullable=False)  # type: Any
    hashed_password = Column(String, nullable=False)  # type: Any
    is_active = Column(Boolean, default=True)  # type: Any
    is_superuser = Column(Boolean, default=False)  # type: Any
    last_login = Column(DateTime(timezone=True), nullable=True)  # type: Any
    email_verified = Column(Boolean, default=False)  # type: Any
    verification_token = Column(String, nullable=True)  # type: Any
    reset_token = Column(String, nullable=True)  # type: Any
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)  # type: Any
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # type: Any
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # type: Any
    is_deleted = Column(Boolean, default=False)  # type: Any
    deleted_at = Column(DateTime(timezone=True))  # type: Any

    # Relationships
    votes = relationship(
        "Vote", back_populates="user", cascade="all, delete-orphan"
    )  # type: Any
    polls = relationship(
        "Poll", back_populates="user", cascade="all, delete-orphan"
    )  # type: Any
    delegations_as_delegator = relationship(
        "Delegation", foreign_keys="Delegation.delegator_id", back_populates="delegator", cascade="all, delete-orphan"
    )
    delegations_as_delegatee = relationship(
        "Delegation", foreign_keys="Delegation.delegatee_id", back_populates="delegatee", cascade="all, delete-orphan"
    )
    comments = relationship(
        "Comment", back_populates="user", cascade="all, delete-orphan"
    )  # type: Any
    comment_reactions = relationship(
        "CommentReaction", back_populates="user", cascade="all, delete-orphan"
    )  # type: Any

    async def soft_delete(self, db_session: Session) -> None:
        """Soft delete the user and all related polls and votes.

        Args:
            db_session: The database session to use for the operation.
        """
        from backend.models.poll import Poll  # Import here to avoid circular dependency
        from backend.models.vote import Vote  # Import here to avoid circular dependency

        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        # Soft delete related polls
        result = await db_session.execute(
            select(Poll).where(Poll.created_by == self.id, Poll.is_deleted == False)
        )
        polls = result.scalars().all()
        for poll in polls:
            await poll.soft_delete(db_session)
        # Soft delete related votes
        result = await db_session.execute(
            select(Vote).where(Vote.user_id == self.id, Vote.is_deleted == False)
        )
        votes = result.scalars().all()
        for vote in votes:
            await vote.soft_delete(db_session)

    def is_user_active(self) -> bool:
        """Check if user is active."""
        return self.is_deleted is False and self.is_active is True

    def is_user_superuser(self) -> bool:
        """Check if user is superuser."""
        return self.is_deleted is False and self.is_superuser is True
