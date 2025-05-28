from datetime import datetime
from typing import Any, List
from uuid import UUID

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from backend.core.types import GUID
from backend.models.base import SQLAlchemyBase




class DelegationStats(SQLAlchemyBase):
    """Model for caching delegation statistics."""

    __tablename__ = "delegation_stats"

    top_delegatees = Column(JSON, nullable=False)  # type: Any
    avg_chain_length = Column(Float, nullable=False)  # type: Any
    longest_chain = Column(Integer, nullable=False)  # type: Any
    active_delegations = Column(Integer, nullable=False)  # type: Any
    calculated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow
    )  # type: Any
    poll_id = Column(GUID(), nullable=True)  # type: Any  # Null for global stats
