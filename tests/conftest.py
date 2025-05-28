"""Test fixtures and configuration."""

import os
import pytest
import pytest_asyncio
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any
from contextlib import asynccontextmanager
from unittest.mock import patch
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from fastapi_limiter import FastAPILimiter

from backend.main import app, get_redis_client
from backend.database import get_db
from backend.core.auth import create_access_token
from backend.models.user import User
from backend.models.poll import Poll
from backend.models.option import Option
from backend.models.vote import Vote
from backend.models.delegation import Delegation
from backend.models.activity_log import ActivityLog

from tests.test_env import setup_test_env, restore_env
from tests.db_config import (
    test_engine,
    test_session_factory,
    init_test_db,
    cleanup_test_db,
    get_test_db,
    reset_test_db,
)
from tests.redis_config import (
    get_test_redis,
    init_test_redis,
    cleanup_test_redis,
    TestRedisClient,
)
from tests.utils import (
    create_test_user,
    cleanup_test_data,
    verify_test_data_cleanup,
    managed_transaction,
)

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_env():
    """Set up and tear down test environment variables."""
    original_env = setup_test_env()
    yield
    restore_env(original_env)

@pytest_asyncio.fixture(scope="function")
async def setup_test_db(test_env):
    """Set up test database tables."""
    logger.info("Setting up test database")
    await init_test_db()
    yield
    logger.info("Cleaning up test database")
    await cleanup_test_db()

@pytest_asyncio.fixture
async def db_session(setup_test_db):
    """Create a fresh database session for a test."""
    logger.debug("Creating new database session")
    async with get_test_db() as session:
        yield session

@pytest.fixture
async def cleanup_test_data_fixture(db_session):
    """Clean up test data after each test."""
    yield
    await reset_test_db()

@pytest_asyncio.fixture
async def redis_client():
    """Create a Redis client for tests."""
    async with get_test_redis() as client:
        yield client.client

@pytest_asyncio.fixture(scope="session", autouse=True)
async def patch_fastapi_limiter():
    """Patch FastAPILimiter.init globally for all tests."""
    with patch('fastapi_limiter.FastAPILimiter.init', return_value=None) as mock_init:
        await mock_init()
        yield mock_init

@pytest_asyncio.fixture
async def client(db_session, redis_client):
    """Create a test client with authentication."""
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis_client] = lambda: redis_client

    # Initialize FastAPILimiter with mock Redis
    await FastAPILimiter.init(redis_client)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def auth_headers(test_user) -> Dict[str, str]:
    """Create authentication headers for the test user."""
    access_token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
async def test_vote(db_session, test_user, auth_headers):
    """Create a test vote with associated poll and option."""
    from tests.utils import create_test_poll_with_options, create_test_vote

    async with managed_transaction(db_session) as session:
        # Create poll with options
        poll, options = await create_test_poll_with_options(session, test_user)

        # Create vote
        vote = await create_test_vote(session, test_user, poll, options[0])

        return {
            "vote_id": str(vote.id),
            "poll_id": str(poll.id),
            "option_id": str(options[0].id),
            "user_id": str(test_user.id),
            "poll": poll,
            "option": options[0],
            "user": test_user,
        }

@pytest.fixture
async def read_only_session(db_session) -> AsyncGenerator[AsyncSession, None]:
    """Create a read-only database session for queries."""
    async with managed_transaction(db_session, readonly=True) as session:
        yield session
