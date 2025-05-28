from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db


async def get_db_session() -> AsyncSession:
    """
    FastAPI dependency for database sessions.
    Uses the async context manager to ensure proper session cleanup.
    """
    async with get_db() as session:
        yield session
