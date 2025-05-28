"""Test health check endpoints."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_root_health_check(client: AsyncClient) -> None:
    """Test the root health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "message": "Service is running"
    }

async def test_database_health_check(client: AsyncClient) -> None:
    """Test the database health check endpoint."""
    response = await client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["message"] == "Database connection is healthy"
    assert data["connection"] == "connected"

async def test_redis_health_check(client: AsyncClient) -> None:
    """Test the Redis health check endpoint."""
    response = await client.get("/health/redis")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["message"] == "Redis connection is healthy"
    assert data["connection"] == "connected"