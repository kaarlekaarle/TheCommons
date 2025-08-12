# from sqlalchemy import event  # Remove this import
# from sqlalchemy.orm import Session  # Remove this import
from typing import Any, AsyncGenerator, Dict

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
from datetime import datetime, timedelta
from uuid import uuid4

import backend.models
from backend.core.auth import create_access_token, get_password_hash
from backend.core.security import get_password_hash as core_get_password_hash
from backend.database import Base, SQLAlchemyBase, get_db
from backend.main import app
from backend.models.poll import Poll
from backend.models.user import User
from fastapi import FastAPI
from sqlalchemy.pool import StaticPool

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

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


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def db_session(event_loop):
    """Create a fresh database for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession, app: FastAPI):
    async def override_get_db():
        try:
            yield db_session
        finally:
            await db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=str(uuid4()),
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def inactive_user(db_session: AsyncSession) -> User:
    """Create an inactive test user."""
    user = User(
        id=str(uuid4()),
        email="inactive@example.com",
        username="inactive",
        hashed_password=get_password_hash("testpassword"),
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_user: User) -> Dict[str, str]:
    """Create authentication headers for the test user."""
    access_token = create_access_token(
        data={"sub": test_user.id},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture(scope="function")
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
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
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
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
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


@pytest_asyncio.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
def app() -> FastAPI:
    from backend.main import app as fastapi_app
    return fastapi_app
