"""Test Redis client singleton pattern and connection pooling."""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
import asyncio
from unittest.mock import patch

from backend.core.redis import get_redis_client, close_redis_client
from tests.redis_config import get_test_redis, TestRedisClient

@pytest.mark.asyncio
async def test_singleton_pattern():
    """Test that Redis client follows singleton pattern."""
    # Get first instance
    client1 = await get_redis_client()
    assert client1 is not None, "First Redis client should not be None"
    
    # Get second instance
    client2 = await get_redis_client()
    assert client2 is not None, "Second Redis client should not be None"
    
    # Verify both instances are the same object
    assert client1 is client2, "Redis client should be a singleton"
    
    # Clean up
    await close_redis_client()

@pytest.mark.asyncio
async def test_connection_pool():
    """Test Redis connection pooling behavior."""
    client = await get_redis_client()
    
    # Test multiple concurrent operations
    async def test_operation():
        return await client.ping()
    
    # Run multiple concurrent operations
    tasks = [test_operation() for _ in range(5)]
    results = await asyncio.gather(*tasks)
    
    # Verify all operations succeeded
    assert all(results), "All concurrent operations should succeed"
    
    # Clean up
    await close_redis_client()

@pytest.mark.asyncio
async def test_client_cleanup():
    """Test Redis client cleanup."""
    # Get client
    client1 = await get_redis_client()
    assert client1 is not None, "Redis client should be initialized"
    
    # Close client
    await close_redis_client()
    
    # Get new client
    client2 = await get_redis_client()
    assert client2 is not None, "New Redis client should be initialized"
    
    # Verify it's a new instance
    assert client1 is not client2, "New client should be a different instance"
    
    # Clean up
    await close_redis_client()

@pytest.mark.asyncio
async def test_mock_redis():
    """Test Redis client with mock Redis."""
    async with get_test_redis(mock=True) as client:
        # Test basic operations with mock Redis
        await client.client.set("test_key", "test_value")
        value = await client.client.get("test_key")
        assert value == b"test_value", "Mock Redis get/set operations failed"
        
        # Test connection pool with mock Redis
        async def test_operation():
            return await client.client.ping()
        
        tasks = [test_operation() for _ in range(3)]
        results = await asyncio.gather(*tasks)
        assert all(results), "All mock Redis operations should succeed"

@pytest.mark.asyncio
async def test_error_handling():
    """Test Redis client error handling."""
    with patch('redis.asyncio.from_url', side_effect=Exception("Connection failed")):
        with pytest.raises(Exception) as exc_info:
            await get_redis_client()
        assert "Connection failed" in str(exc_info.value), "Should raise connection error" 