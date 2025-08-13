"""Test fixtures and configuration for offline, self-contained test suite."""

import os
import pytest
import pytest_asyncio
import asyncio
import logging
import time
from typing import AsyncGenerator, Dict, Any, Optional
from contextlib import asynccontextmanager
from unittest.mock import patch, AsyncMock
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import MetaData, text
from httpx import AsyncClient
from fastapi import FastAPI

from backend.main import app
from backend.database import get_db
from backend.core.auth import create_access_token
from backend.core.redis import get_redis_client, close_redis_client
from backend.models.user import User
from backend.models.poll import Poll
from backend.models.option import Option
from backend.models.vote import Vote
from backend.models.delegation import Delegation
from backend.models.activity_log import ActivityLog
from backend.models.comment import Comment
from backend.models.comment_reaction import CommentReaction

logger = logging.getLogger(__name__)

# Configure logging to capture WARNING and above
@pytest.fixture(autouse=True)
def configure_logging(caplog):
    """Configure logging to capture WARNING and above."""
    caplog.set_level(logging.WARNING)
    return caplog

class FakeRedis:
    """In-memory Redis implementation with TTL support."""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value from Redis."""
        if key in self._expiry and time.time() > self._expiry[key]:
            del self._data[key]
            del self._expiry[key]
            return None
        return self._data.get(key)
    
    async def setex(self, key: str, ttl: int, value: str) -> bool:
        """Set a value with TTL."""
        self._data[key] = value
        self._expiry[key] = time.time() + ttl
        return True
    
    async def incr(self, key: str) -> int:
        """Increment a counter."""
        current = await self.get(key)
        if current is None:
            new_value = 1
        else:
            new_value = int(current) + 1
        await self.setex(key, 60, str(new_value))  # Default 60s TTL
        return new_value
    
    async def ttl(self, key: str) -> int:
        """Get TTL for a key."""
        if key not in self._expiry:
            return -1
        remaining = self._expiry[key] - time.time()
        return max(0, int(remaining))
    
    async def delete(self, *keys: str) -> int:
        """Delete keys."""
        deleted = 0
        for key in keys:
            if key in self._data:
                del self._data[key]
                if key in self._expiry:
                    del self._expiry[key]
                deleted += 1
        return deleted
    
    async def close(self):
        """Close the fake Redis connection."""
        self._data.clear()
        self._expiry.clear()

@pytest.fixture
def fake_redis():
    """Create a fake Redis instance for testing."""
    return FakeRedis()

@pytest.fixture
def app_with_fake_redis(fake_redis):
    """Create the FastAPI app with fake Redis dependency override."""
    # Override Redis dependency
    app.dependency_overrides[get_redis_client] = lambda: fake_redis
    yield app
    # Cleanup
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def async_client(app_with_fake_redis):
    """Create an async HTTP client with lifespan support."""
    async with AsyncClient(app=app_with_fake_redis, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def db_engine():
    """Create an in-memory SQLite database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session_factory(db_engine):
    """Create a database session factory."""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    return async_session

@pytest_asyncio.fixture
async def db_session(db_session_factory):
    """Create a database session for testing."""
    async with db_session_factory() as session:
        # Create tables
        async with db_engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_superuser BOOLEAN DEFAULT FALSE,
                    last_login DATETIME,
                    email_verified BOOLEAN DEFAULT FALSE,
                    verification_token TEXT,
                    reset_token TEXT,
                    reset_token_expires DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    deleted_at DATETIME
                )
            """)))
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("""
                CREATE TABLE IF NOT EXISTS polls (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    created_by TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    deleted_at DATETIME,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """)))
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("""
                CREATE TABLE IF NOT EXISTS options (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    poll_id TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    deleted_at DATETIME,
                    FOREIGN KEY (poll_id) REFERENCES polls (id)
                )
            """)))
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("""
                CREATE TABLE IF NOT EXISTS votes (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    poll_id TEXT NOT NULL,
                    option_id TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    deleted_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (poll_id) REFERENCES polls (id),
                    FOREIGN KEY (option_id) REFERENCES options (id)
                )
            """)))
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("""
                CREATE TABLE IF NOT EXISTS delegations (
                    id TEXT PRIMARY KEY,
                    delegator_id TEXT NOT NULL,
                    delegate_id TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    deleted_at DATETIME,
                    FOREIGN KEY (delegator_id) REFERENCES users (id),
                    FOREIGN KEY (delegate_id) REFERENCES users (id)
                )
            """)))
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("""
                CREATE TABLE IF NOT EXISTS comments (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    poll_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    deleted_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (poll_id) REFERENCES polls (id)
                )
            """)))
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("""
                CREATE TABLE IF NOT EXISTS comment_reactions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    comment_id TEXT NOT NULL,
                    reaction_type TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    deleted_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (comment_id) REFERENCES comments (id)
                )
            """)))
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT,
                    details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)))
        
        # Override database dependency
        app.dependency_overrides[get_db] = lambda: session
        yield session
        # Cleanup
        app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(test_user) -> Dict[str, str]:
    """Create authentication headers for the test user."""
    access_token = create_access_token(
        data={"sub": str(test_user.id)},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    import uuid
    from backend.core.security import get_password_hash
    
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_poll(db_session, test_user):
    """Create a test poll."""
    import uuid
    
    poll_id = str(uuid.uuid4())
    poll = Poll(
        id=poll_id,
        title="Test Poll",
        description="Test Description",
        created_by=test_user.id
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)
    return poll

@pytest.fixture
async def test_option(db_session, test_poll):
    """Create a test option."""
    import uuid
    
    option_id = str(uuid.uuid4())
    option = Option(
        id=option_id,
        text="Test Option",
        poll_id=test_poll.id
    )
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)
    return option

@pytest.fixture
async def test_vote(db_session, test_user, test_poll, test_option):
    """Create a test vote."""
    import uuid
    
    vote_id = str(uuid.uuid4())
    vote = Vote(
        id=vote_id,
        user_id=test_user.id,
        poll_id=test_poll.id,
        option_id=test_option.id
    )
    db_session.add(vote)
    await db_session.commit()
    await db_session.refresh(vote)
    return vote

@pytest.fixture
async def test_delegation(db_session, test_user):
    """Create a test delegation."""
    import uuid
    
    # Create a delegate user
    delegate_id = str(uuid.uuid4())
    delegate = User(
        id=delegate_id,
        email="delegate@example.com",
        username="delegate",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(delegate)
    
    # Create delegation
    delegation_id = str(uuid.uuid4())
    delegation = Delegation(
        id=delegation_id,
        delegator_id=test_user.id,
        delegate_id=delegate.id
    )
    db_session.add(delegation)
    await db_session.commit()
    await db_session.refresh(delegation)
    return delegation

@pytest.fixture
async def test_comment(db_session, test_user, test_poll):
    """Create a test comment."""
    import uuid
    
    comment_id = str(uuid.uuid4())
    comment = Comment(
        id=comment_id,
        user_id=test_user.id,
        poll_id=test_poll.id,
        content="Test comment"
    )
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)
    return comment
