"""Test user service functionality."""

import uuid
from datetime import datetime
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.core.auth import get_password_hash
from backend.core.exceptions import (
    AuthenticationError,
    ResourceNotFoundError,
    UserAlreadyExistsError,
)
from backend.database import get_db
from backend.main import app
from backend.models.base import Base
from backend.models.user import User
from backend.schemas.user import UserCreate, UserUpdate
from backend.services.user import UserService
from tests.config import (
    TEST_DATABASE_URL,
    TEST_ENGINE_SETTINGS,
    TEST_SESSION_SETTINGS,
)
from tests.utils import (
    create_test_user,
    cleanup_test_data,
    verify_test_data_cleanup,
)

# Create test engine
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for a test."""
    from tests.conftest import async_session_factory
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        try:
            yield db_session
        finally:
            await db_session.rollback()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_data_fixture(db_session):
    """Clean up test data after each test."""
    yield
    await cleanup_test_data(db_session)
    assert await verify_test_data_cleanup(db_session), "Test data cleanup failed"


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> AsyncGenerator[User, None]:
    username = f"testuser_{uuid.uuid4()}"
    email = f"{username}@example.com"
    password = "testpassword"
    now = datetime.utcnow()
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        is_active=True,
        is_superuser=False,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    yield user


@pytest_asyncio.fixture
async def user_service(db_session: AsyncSession) -> UserService:
    """Create a UserService instance for testing."""
    return UserService(db_session)


@pytest.mark.asyncio
async def test_create_user(user_service: UserService) -> None:
    """Test user creation."""
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="TestPassword123!",
    )
    user = await user_service.create_user(user_data)
    assert user.email == user_data.email
    assert user.username == user_data.username
    assert user.is_active is True


@pytest.mark.asyncio
async def test_get_user(user_service: UserService, test_user: User) -> None:
    """Test getting a user."""
    user = await user_service.get_user(test_user.id)
    assert user.id == test_user.id
    assert user.email == test_user.email
    assert user.username == test_user.username


@pytest.mark.asyncio
async def test_get_user_not_found(user_service: UserService) -> None:
    """Test getting a non-existent user."""
    with pytest.raises(ResourceNotFoundError):
        await user_service.get_user(999)


@pytest.mark.asyncio
async def test_update_user(user_service: UserService, test_user: User) -> None:
    """Test updating a user."""
    update_data = UserUpdate(
        email="updated@example.com",
        username="updateduser",
    )
    updated_user = await user_service.update_user(test_user.id, update_data)
    assert updated_user.email == update_data.email
    assert updated_user.username == update_data.username


@pytest.mark.asyncio
async def test_delete_user(user_service: UserService, test_user: User) -> None:
    """Test deleting a user."""
    await user_service.delete_user(test_user.id)
    with pytest.raises(ResourceNotFoundError):
        await user_service.get_user(test_user.id)


@pytest.mark.asyncio
async def test_authenticate_user(user_service: UserService, test_user: User) -> None:
    """Test user authentication."""
    user = await user_service.authenticate_user(
        test_user.username, "TestPassword123!"
    )
    assert user.id == test_user.id
    assert user.username == test_user.username


@pytest.mark.asyncio
async def test_authenticate_user_invalid_password(
    user_service: UserService, test_user: User
) -> None:
    """Test authentication with invalid password."""
    with pytest.raises(AuthenticationError):
        await user_service.authenticate_user(test_user.username, "wrongpassword")


@pytest.mark.asyncio
async def test_get_users(user_service: UserService, test_user: User) -> None:
    """Test getting list of users."""
    users = await user_service.get_users()
    assert len(users) > 0
    assert any(user.id == test_user.id for user in users)


@pytest.mark.asyncio
async def test_get_users_with_search(
    user_service: UserService, test_user: User
) -> None:
    """Test getting users with search term."""
    users = await user_service.get_users(search=test_user.username)
    assert len(users) > 0
    assert all(test_user.username in user.username for user in users)


@pytest.mark.asyncio
async def test_create_user_duplicate_username(
    user_service: UserService, test_user: User
) -> None:
    """Test creating user with duplicate username."""
    user_data = UserCreate(
        email="different@example.com",
        username=test_user.username,
        password="TestPassword123!",
    )
    with pytest.raises(UserAlreadyExistsError):
        await user_service.create_user(user_data)


@pytest.mark.asyncio
async def test_create_user_duplicate_email(
    user_service: UserService, test_user: User
) -> None:
    """Test creating user with duplicate email."""
    user_data = UserCreate(
        email=test_user.email,
        username="differentuser",
        password="TestPassword123!",
    )
    with pytest.raises(UserAlreadyExistsError):
        await user_service.create_user(user_data)
