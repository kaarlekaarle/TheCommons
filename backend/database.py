import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

# Import Base from models
from backend.models.base import Base, SQLAlchemyBase

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Get database configuration from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/the_commons"
)
DB_ECHO_LOG = os.getenv("DB_ECHO_LOG", "false").lower() == "true"

# Create async engine for PostgreSQL or SQLite
if DATABASE_URL.startswith("sqlite"):
    from sqlalchemy.pool import StaticPool

    engine = create_async_engine(
        DATABASE_URL,
        echo=DB_ECHO_LOG,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=DB_ECHO_LOG,
        future=True,
        pool_pre_ping=True,  # Enable connection health checks
        pool_size=5,  # Set reasonable pool size
        max_overflow=10,  # Allow some overflow connections
    )

# Create async session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Add event listener to filter out soft-deleted records
@event.listens_for(Session, "do_orm_execute")


def _add_soft_delete_filter(execute_state):
    """Add soft delete filter to all queries."""
    if execute_state.is_select and not execute_state.is_column_load:
        # Get the query
        query = execute_state.statement

        # Add soft delete filter for SQLAlchemyBase models
        for entity in query._raw_columns:
            if hasattr(entity, "entity") and issubclass(entity.entity, SQLAlchemyBase):
                query = query.where(entity.entity.is_deleted.is_(False))
                execute_state.statement = query


async def init_db() -> None:
    """Initialize the database by creating all tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to initialize database", extra={"error": str(e)})
        raise


async def get_db() -> AsyncSession:
    """
    FastAPI dependency for database sessions.
    Automatically handles session cleanup and rollback on errors.

    Yields:
        AsyncSession: A database session

    Raises:
        Exception: If there's an error during session management
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Database error in session", extra={"error": str(e)})
            await session.rollback()
            raise
        finally:
            await session.close()
