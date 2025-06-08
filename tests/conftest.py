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

from backend.main import app
from backend.database import get_db
from backend.core.auth import create_access_token
from backend.core.redis import get_redis_client, close_redis_client
from backend.core.rate_limiting import RateLimitTier, RATE_LIMITS
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

@pytest_asyncio.fixture(scope="function", autouse=True)
async def override_rate_limits():
    """Override rate limits for testing to be more permissive."""
    from backend.core.rate_limiting import RATE_LIMITS, RateLimitTier, get_rate_limiter
    from unittest.mock import AsyncMock, patch
    from fastapi import Depends
    from fastapi_limiter.depends import RateLimiter
    import fastapi_limiter
    
    # Store original limits
    original_limits = RATE_LIMITS.copy()
    
    # Set test-specific limits
    RATE_LIMITS.update({
        RateLimitTier.PUBLIC: {"times": 1000, "minutes": 1},
        RateLimitTier.AUTHENTICATED: {"times": 1000, "minutes": 1},
        RateLimitTier.SENSITIVE: {"times": 1000, "seconds": 60},
        RateLimitTier.ADMIN: {"times": 1000, "minutes": 1}
    })
    
    # Create an async mock that always returns True
    async def mock_rate_limiter(*args, **kwargs):
        return True
    
    # Create a mock RateLimiter class
    class MockRateLimiter:
        def __init__(self, *args, **kwargs):
            pass
        async def __call__(self, request, response):
            return True
    
    # Dummy callables for FastAPILimiter attributes
    async def dummy_identifier(request):
        return "dummy-key"
    async def dummy_callback(request, response, p1=None, p2=None):
        return None
    
    # Patch get_rate_limiter, RateLimiter, and FastAPILimiter attributes
    with patch('backend.core.rate_limiting.get_rate_limiter', 
              lambda tier: Depends(mock_rate_limiter)), \
         patch('fastapi_limiter.depends.RateLimiter', MockRateLimiter), \
         patch.object(fastapi_limiter.FastAPILimiter, 'redis', new=AsyncMock()), \
         patch.object(fastapi_limiter.FastAPILimiter, 'identifier', new=dummy_identifier), \
         patch.object(fastapi_limiter.FastAPILimiter, 'http_callback', new=dummy_callback), \
         patch.object(fastapi_limiter.FastAPILimiter, 'ws_callback', new=dummy_callback):
        yield
    
    # Restore original limits
    RATE_LIMITS.clear()
    RATE_LIMITS.update(original_limits)

@pytest_asyncio.fixture
async def client(db_session, redis_client):
    """Create a test client with authentication."""
    # Override dependencies
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis_client] = lambda: redis_client

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Cleanup
    app.dependency_overrides.clear()
    await close_redis_client()

@pytest_asyncio.fixture
def auth_headers(test_user) -> Dict[str, str]:
    """Create authentication headers for the test user."""
    access_token = create_access_token(
        data={"sub": str(test_user.id)},
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

# Test rate limit configurations
@pytest.fixture
def test_rate_limits():
    """Get test rate limit configurations."""
    return {
        RateLimitTier.PUBLIC: {"times": 100, "minutes": 1},
        RateLimitTier.AUTHENTICATED: {"times": 200, "minutes": 1},
        RateLimitTier.SENSITIVE: {"times": 10, "seconds": 60},
        RateLimitTier.ADMIN: {"times": 500, "minutes": 1},
    }
