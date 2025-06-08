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
from sqlalchemy.pool import StaticPool
from sqlalchemy import event, text

from backend.models.base import Base, SQLAlchemyBase

logger = logging.getLogger(__name__)

# Test database configuration
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test.db")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

# Engine settings
TEST_ENGINE_SETTINGS = {
    "echo": True,  # Enable SQL logging for tests
    "future": True,
    "connect_args": {"check_same_thread": False},
    "poolclass": StaticPool,  # Use static pool for SQLite
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
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Test database cleaned up successfully")
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
        async with test_engine.begin() as conn:
            # Drop all tables
            await conn.run_sync(Base.metadata.drop_all)
            # Recreate all tables
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Test database reset successfully")
    except Exception as e:
        logger.error(f"Failed to reset test database: {e}")
        raise 