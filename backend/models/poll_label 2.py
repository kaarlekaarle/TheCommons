from sqlalchemy import Column, ForeignKey, Table
from backend.core.types import GUID
from backend.models.base import Base

# Association table for Poll ↔ Label many-to-many relationship
poll_labels = Table(
    "poll_labels",
    Base.metadata,
    Column("poll_id", GUID(), ForeignKey("polls.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", GUID(), ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)
