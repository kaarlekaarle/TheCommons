# from sqlalchemy import event  # Remove this import
# from sqlalchemy.orm import Session  # Remove this import
from typing import Any, AsyncGenerator, Dict

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import backend.models
from backend.core.auth import create_access_token, get_password_hash
from backend.core.security import get_password_hash as core_get_password_hash
from backend.database import Base, SQLAlchemyBase, get_db
from backend.main import app
from backend.models.poll import Poll
from backend.models.user import User

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Create test session
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Remove the event listener for soft delete filtering
# @event.listens_for(Session, 'do_orm_execute')
# def _add_soft_delete_filter(execute_state):
#     """Add soft delete filter to all queries."""
#     if execute_state.is_select and not execute_state.is_column_load:
#         # Get the query
#         query = execute_state.statement
#         # Add soft delete filter for SQLAlchemyBase models
#         for entity in query._raw_columns:
#             if hasattr(entity, 'entity') and issubclass(entity.entity, SQLAlchemyBase):
#                 query = query.where(entity.entity.is_deleted == False)
#                 execute_state.statement = query


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[TestClient, None]:
    """Create a test client with a database session."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def auth_headers(test_user: User) -> Dict[str, str]:
    """Create authentication headers for a test user."""
    access_token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
async def test_user2(db_session: AsyncSession) -> User:
    """Create a second test user."""
    user = User(
        email="test2@example.com",
        username="testuser2",
        hashed_password=get_password_hash("TestPassword123!"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture(scope="function")
async def test_user3(db_session: AsyncSession) -> User:
    """Create a third test user."""
    user = User(
        email="test3@example.com",
        username="testuser3",
        hashed_password=get_password_hash("TestPassword123!"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture(scope="function")
async def test_poll(db_session: AsyncSession, test_user: User) -> Poll:
    """Create a test poll."""
    poll = Poll(
        title="Test Poll",
        description="A poll for testing",
        created_by=test_user.id,
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)
    return poll
