import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index

from backend.core.types import GUID
from backend.models.base import SQLAlchemyBase




class ActionType(str, Enum):
    VOTE = "vote"
    DELEGATION_CREATED = "delegation_created"
    DELEGATION_REVOKED = "delegation_revoked"
    POLL_CREATED = "poll_created"




class ActivityLog(SQLAlchemyBase):
    __tablename__ = "activitylog"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)  # type: Any
    user_id = Column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )  # type: Any
    action_type = Column(SQLEnum(ActionType), nullable=False)  # type: Any
    reference_id = Column(GUID(), nullable=False)  # type: Any
    meta = Column(JSON, nullable=True)  # type: Any

    __table_args__ = (
        Index("ix_activitylog_timestamp", "created_at"),
        Index("ix_activitylog_user_id", "user_id"),
        Index("ix_activitylog_action_type", "action_type"),
        Index("ix_activitylog_reference_id", "reference_id"),
    )

    async def soft_delete(self, db_session):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
