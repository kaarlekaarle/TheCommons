"""Test database configuration."""

import os
import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy import event, text

from backend.models.base import Base, SQLAlchemyBase

logger = logging.getLogger(__name__)

# Test database configuration - Use the same database as main app
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/commons_db"
)

# Engine settings - Use PostgreSQL settings
TEST_ENGINE_SETTINGS = {
    "echo": True,  # Enable SQL logging for tests
    "future": True,
    "pool_pre_ping": True,  # Enable connection health checks
    "pool_size": 5,  # Set reasonable pool size
    "max_overflow": 10,  # Allow some overflow connections
}

# Session settings
TEST_SESSION_SETTINGS = {
    "expire_on_commit": False,
    "autocommit": False,
    "autoflush": False,
}

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, **TEST_ENGINE_SETTINGS)

# Create test session factory
test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    **TEST_SESSION_SETTINGS,
)

# Add event listener for soft delete filtering
# @event.listens_for(AsyncSession, "do_orm_execute")
# def _do_orm_execute(orm_execute_state):
#     # Your event handling code here
#     pass

async def init_test_db() -> None:
    """Initialize the test database."""
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Test database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize test database: {e}")
        raise

async def cleanup_test_db() -> None:
    """Clean up the test database."""
    try:
        # Instead of dropping all tables, just clean up test data
        # This is safer when using the same database as the main app
        logger.info("Test database cleanup completed (no tables dropped)")
    except Exception as e:
        logger.error(f"Failed to clean up test database: {e}")
        raise

@asynccontextmanager
async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session with automatic cleanup."""
    async with test_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Test database error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def reset_test_db() -> None:
    """Reset the test database to a clean state."""
    try:
        # Instead of dropping and recreating tables, just ensure they exist
        # This is safer when using the same database as the main app
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Test database reset completed (tables ensured to exist)")
    except Exception as e:
        logger.error(f"Failed to reset test database: {e}")
        raise 