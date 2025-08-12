"""Comment reaction model for The Commons."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import SQLAlchemyBase


class ReactionType(str, Enum):
    """Reaction types."""
    UP = "up"
    DOWN = "down"


class CommentReaction(SQLAlchemyBase):
    """Comment reaction model."""
    __tablename__ = "comment_reactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # type: Any
    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True)  # type: Any
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # type: Any
    type = Column(SQLEnum(ReactionType), nullable=False)  # type: Any
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # type: Any

    # Relationships
    comment = relationship("Comment", back_populates="reactions")  # type: Any
    user = relationship("User", back_populates="comment_reactions")  # type: Any

    # Constraints
    __table_args__ = (
        UniqueConstraint('comment_id', 'user_id', name='uq_comment_user_reaction'),
    )
