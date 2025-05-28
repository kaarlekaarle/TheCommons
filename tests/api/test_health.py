"""Test health check endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from unittest.mock import AsyncMock
from backend.main import app, get_redis_client
import pytest_asyncio

from tests.config import logger

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test the basic health check endpoint."""
    logger.info("Testing basic health check endpoint")
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "message" in data
    assert data["message"] == "Service is running"

@pytest.mark.asyncio
async def test_db_health_check(client: AsyncClient, db_session: AsyncSession):
    """Test the database health check endpoint."""
    logger.info("Testing database health check endpoint")
    response = await client.get("/health/db")
    print("DB health check response:", response.text)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "message" in data
    assert data["message"] == "Database connection is healthy"
    assert data["connection"] == "connected"

@pytest.mark.asyncio
async def test_redis_health_check(client: AsyncClient, redis_client):
    """Test the Redis health check endpoint."""
    logger.info("Testing Redis health check endpoint")
    response = await client.get("/health/redis")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "message" in data
    assert data["message"] == "Redis connection is healthy"
    assert data["connection"] == "connected"

@pytest.mark.asyncio
async def test_db_health_check_failure(client: AsyncClient, monkeypatch):
    """Test database health check when database is unavailable."""
    logger.info("Testing database health check failure scenario")
    # Patch async_session_maker to raise an exception
    async def broken_session_maker(*args, **kwargs):
        raise Exception("Simulated DB failure")
    monkeypatch.setattr("backend.main.async_session_maker", broken_session_maker)
    response = await client.get("/health/db")
    print("DB health check failure response:", response.text)
    assert response.status_code == 503
    data = response.json()
    detail = data["detail"]
    assert detail["status"] == "unhealthy"
    assert "message" in detail
    assert detail["message"] == "Database connection error"
    assert "error" in detail
    assert detail["connection"] == "disconnected"

@pytest.mark.asyncio
async def test_redis_health_check_failure(monkeypatch):
    """Test Redis health check when Redis is unavailable."""
    logger.info("Testing Redis health check failure scenario")
    from httpx import AsyncClient
    # Patch get_redis_client to return a mock client whose ping fails
    class BrokenRedis:
        async def ping(self):
            raise Exception("Simulated Redis failure")
    async def broken_get_redis_client():
        return BrokenRedis()
    app.dependency_overrides[get_redis_client] = broken_get_redis_client
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health/redis")
        print("Redis health check failure response:", response.text)
        assert response.status_code == 503
        data = response.json()
        detail = data["detail"]
        assert detail["status"] == "unhealthy"
        assert "message" in detail
        assert detail["message"] == "Redis connection error"
        assert "error" in detail
        assert detail["connection"] == "disconnected"
    app.dependency_overrides = {}