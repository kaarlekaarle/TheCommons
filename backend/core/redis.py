"""Redis client management module."""

import redis.asyncio as redis
from typing import Optional
from backend.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

# Global Redis client instance with connection pooling
_redis_client: Optional[redis.Redis] = None

async def get_redis_client() -> redis.Redis:
    """
    Get the Redis client instance with connection pooling.
    Creates the client if it doesn't exist.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=100,  # Adjust based on your needs
            socket_timeout=5.0,   # 5 second timeout
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
            health_check_interval=30,  # Check connection health every 30 seconds
        )
        logger.info("Redis client initialized with connection pooling")
    return _redis_client

async def close_redis_client() -> None:
    """Close the Redis client connection pool."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client connection pool closed") 