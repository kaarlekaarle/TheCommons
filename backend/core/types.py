import uuid
from typing import Any, Optional

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, Text, TypeDecorator
import asyncpg




class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise stores as CHAR(32).
    Compatible with asyncpg + Pydantic v2.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, asyncpg.pgproto.pgproto.UUID):  # asyncpg raw UUID
            return str(uuid.UUID(str(value)))
        return str(uuid.UUID(str(value)))
