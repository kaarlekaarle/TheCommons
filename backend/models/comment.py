from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.models.base import Base


class Comment(Base):
    """Comment model for proposal discussions."""
    
    __tablename__ = "comments"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    poll_id = Column(UUID(as_uuid=True), ForeignKey("polls.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Content
    body = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    poll = relationship("Poll", back_populates="comments")
    user = relationship("User", back_populates="comments")
    reactions = relationship("CommentReaction", back_populates="comment", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("ix_comments_poll_id_created_at", "poll_id", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index("ix_comments_user_id", "user_id"),
        Index("ix_comments_is_deleted", "is_deleted"),
    )
    
    def __repr__(self):
        return f"<Comment(id={self.id}, poll_id={self.poll_id}, user_id={self.user_id})>"
