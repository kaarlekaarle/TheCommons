import asyncio
import os
import sys
from datetime import datetime
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import get_password_hash
from backend.main import app
from backend.models.poll import Poll
from backend.models.user import User

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_ready() -> None:
    """Ensure database schema exists before any tests run."""
    import os
    from backend.database import init_db
    
    os.environ["TESTING"] = "true"
    await init_db()
    yield


@pytest_asyncio.fixture(scope="session")
async def db_session(db_ready) -> AsyncGenerator:
    """Create a database session for testing."""
    from backend.database import get_db

    async for session in get_db():
        yield session


@pytest_asyncio.fixture
async def client(db_ready):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpass"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user2(db_session: AsyncSession) -> User:
    """Create a second test user."""
    user = User(
        id=uuid4(),
        email="test2@example.com",
        username="testuser2",
        hashed_password=get_password_hash("testpass"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user3(db_session: AsyncSession) -> User:
    """Create a third test user."""
    user = User(
        id=uuid4(),
        email="test3@example.com",
        username="testuser3",
        hashed_password=get_password_hash("testpass"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_poll(db_session: AsyncSession, test_user: User) -> Poll:
    """Create a test poll."""
    poll = Poll(
        id=uuid4(),
        title="Test Poll",
        description="Test Description",
        created_by=test_user.id,
        status="active",
        visibility="public",
        start_date=datetime.utcnow(),
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)
    return poll
