import pytest
import os
from httpx import AsyncClient
from unittest.mock import patch

from backend.main import app
from backend.core.limiter import limiter_health, get_limiter


@pytest.mark.asyncio
async def test_limiter_health_noop():
    """Test limiter health when Redis is not available."""
    with patch.dict(os.environ, {"REDIS_URL": "", "RATE_LIMIT_ENABLED": "true"}):
        health = limiter_health()
        assert health["enabled"] is False
        assert health["backend"] == "noop"


@pytest.mark.asyncio
async def test_limiter_health_redis():
    """Test limiter health when Redis is available."""
    with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379/0", "RATE_LIMIT_ENABLED": "true"}):
        # This would require actual Redis connection to test fully
        # For now, we test the structure
        health = limiter_health()
        assert "enabled" in health
        assert "backend" in health


@pytest.mark.asyncio
async def test_limiter_disabled():
    """Test limiter when explicitly disabled."""
    with patch.dict(os.environ, {"RATE_LIMIT_ENABLED": "false"}):
        health = limiter_health()
        assert health["enabled"] is False
        assert health["backend"] == "noop"


@pytest.mark.asyncio
async def test_auth_rate_limiting_with_redis():
    """Test that auth endpoint respects rate limits when Redis is available."""
    # This test requires a running Redis instance
    # It would make 6 requests and expect the 6th to be rate limited
    if not os.getenv("REDIS_URL"):
        pytest.skip("Redis not available for rate limiting test")
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Make 5 requests (should succeed)
        for i in range(5):
            response = await ac.post("/api/token", data={
                "username": "testuser",
                "password": "wrongpassword"
            })
            # Should get 401 (wrong credentials) but not 429 (rate limited)
            assert response.status_code == 401
        
        # 6th request should be rate limited
        response = await ac.post("/api/token", data={
            "username": "testuser",
            "password": "wrongpassword"
        })
        assert response.status_code == 429


@pytest.mark.asyncio
async def test_auth_no_rate_limiting_without_redis():
    """Test that auth endpoint doesn't rate limit when Redis is not available."""
    with patch.dict(os.environ, {"REDIS_URL": "", "RATE_LIMIT_ENABLED": "true"}):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Make 10 requests - none should be rate limited
            for i in range(10):
                response = await ac.post("/api/token", data={
                    "username": "testuser",
                    "password": "wrongpassword"
                })
                # Should get 401 (wrong credentials) but never 429 (rate limited)
                assert response.status_code == 401


@pytest.mark.asyncio
async def test_limiter_health_endpoint():
    """Test the limiter health endpoint (requires admin access)."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/limiter/health")
        # Should require authentication
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_limiter():
    """Test that get_limiter returns a limiter instance."""
    limiter = get_limiter()
    assert hasattr(limiter, 'limit')
    assert callable(limiter.limit)
