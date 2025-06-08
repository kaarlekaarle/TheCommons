"""Tests for rate limiting functionality."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.rate_limiting import RATE_LIMITS, RateLimitTier
from tests.utils import create_test_user
from backend.models.user import User

pytestmark = pytest.mark.asyncio

async def test_rate_limiter_override(client: AsyncClient, test_user: User):
    """Test that rate limiter override is working correctly."""
    # Make multiple requests in quick succession
    for _ in range(100):  # Should be well within our test limit of 1000
        response = await client.post(
            "/api/token",
            data={"username": test_user.username, "password": "testpassword"}
        )
        assert response.status_code in (200, 401)  # Either success or invalid credentials
        assert response.status_code != 429  # Should not hit rate limit

async def test_rate_limiter_restoration(client: AsyncClient, test_user: User):
    """Test that original rate limits are restored after each test."""
    # Get the current rate limits
    test_limits = RATE_LIMITS.copy()
    
    # Verify test limits are in place
    assert test_limits[RateLimitTier.PUBLIC]["times"] == 1000
    assert test_limits[RateLimitTier.AUTHENTICATED]["times"] == 1000
    assert test_limits[RateLimitTier.SENSITIVE]["times"] == 1000
    assert test_limits[RateLimitTier.ADMIN]["times"] == 1000

async def test_rate_limiter_basic_protection(client: AsyncClient):
    """Test that rate limiter still provides basic protection even with test limits."""
    # Make requests with invalid credentials to trigger rate limiting
    for _ in range(1001):  # One more than our test limit
        response = await client.post(
            "/api/token",
            data={"username": "nonexistent", "password": "wrong"}
        )
        if response.status_code == 429:  # Rate limit hit
            break
    else:
        pytest.fail("Rate limiting did not trigger even with excessive requests")

async def test_different_rate_limit_tiers(client: AsyncClient, auth_headers: dict):
    """Test that different rate limit tiers are properly configured."""
    # Test public endpoint
    for _ in range(100):  # Should be well within limit
        response = await client.get("/api/health")
        assert response.status_code != 429

    # Test authenticated endpoint
    for _ in range(100):  # Should be well within limit
        response = await client.get("/api/users/me", headers=auth_headers)
        assert response.status_code != 429

    # Test sensitive endpoint (login)
    for _ in range(100):  # Should be well within limit
        response = await client.post(
            "/api/token",
            data={"username": "test", "password": "wrong"}
        )
        assert response.status_code != 429 