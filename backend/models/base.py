import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base

from backend.core.types import GUID

Base = declarative_base()




class SQLAlchemyBase(Base):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)  # type: Any
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # type: Any
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )  # type: Any
    is_deleted = Column(Boolean, default=False, nullable=False)  # type: Any
    deleted_at = Column(DateTime, nullable=True)  # type: Any

    def soft_delete(self) -> None:
        """Soft delete the record.

        Sets is_deleted to True and deleted_at to current time.
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None

    def get_active_query(self):
        """Get query for active records."""
        return self.__class__.query.filter(self.is_deleted is False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
