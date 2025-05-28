import uuid
from typing import Any, Optional

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import CHAR, Text, TypeDecorator




class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise stores as TEXT.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect) -> TypeDecorator:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(Text)

    def process_bind_param(self, value: Any, dialect) -> Optional[str]:
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        else:
            if isinstance(value, int):
                # Convert integer to UUID string format
                return str(uuid.UUID(int=value))
            elif not isinstance(value, uuid.UUID):
                try:
                    return str(uuid.UUID(value))
                except (ValueError, AttributeError):
                    # If conversion fails, try to create a UUID from the integer value
                    return str(uuid.UUID(int=int(value)))
            else:
                return str(value)

    def process_result_value(self, value: Any, dialect) -> Optional[uuid.UUID]:
        if value is None:
            return value
        return uuid.UUID(value)
