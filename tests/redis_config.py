"""Test Redis configuration."""

import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from fakeredis import FakeRedis
import redis.asyncio as aioredis
from fastapi_limiter import FastAPILimiter

logger = logging.getLogger(__name__)

# Redis configuration
TEST_REDIS_URL = "redis://localhost:6379/1"  # Use database 1 for tests
TEST_REDIS_MOCK = True  # Use mock Redis by default

class TestRedisClient:
    """Test Redis client wrapper with additional functionality."""
    
    def __init__(self, mock: bool = True):
        self.mock = mock
        self.client = None
        
    async def init(self) -> None:
        """Initialize the Redis client."""
        try:
            if self.mock:
                self.client = FakeRedis(retry_on_timeout=False)
                self.client.is_mock = True
            else:
                self.client = await aioredis.from_url(TEST_REDIS_URL)
                self.client.is_mock = False
            logger.info(f"Redis client initialized (mock: {self.mock})")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise
            
    async def close(self) -> None:
        """Close the Redis client."""
        if self.client and not self.mock:
            await self.client.close()
            logger.info("Redis client closed")
            
    async def flush(self) -> None:
        """Flush all data from Redis."""
        if self.client:
            await self.client.flushall()
            logger.info("Redis data flushed")
            
    async def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            if self.mock:
                return True
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

@asynccontextmanager
async def get_test_redis(mock: bool = TEST_REDIS_MOCK) -> AsyncGenerator[TestRedisClient, None]:
    """Get a test Redis client with automatic cleanup."""
    client = TestRedisClient(mock=mock)
    try:
        await client.init()
        yield client
    finally:
        await client.close()

async def init_test_redis(mock: bool = TEST_REDIS_MOCK) -> TestRedisClient:
    """Initialize test Redis client."""
    client = TestRedisClient(mock=mock)
    await client.init()
    return client

async def cleanup_test_redis(client: TestRedisClient) -> None:
    """Clean up test Redis data."""
    await client.flush()
    await client.close() 