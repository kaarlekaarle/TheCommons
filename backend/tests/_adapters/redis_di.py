"""Redis dependency injection adapter for testing rate limiting."""

from typing import Optional
import redis.asyncio as redis

# Global Redis client instance for testing
_test_redis_client: Optional[redis.Redis] = None

def get_test_redis_client() -> Optional[redis.Redis]:
    """Get the test Redis client instance."""
    return _test_redis_client

def set_test_redis_client(client: Optional[redis.Redis]) -> None:
    """Set the test Redis client instance."""
    global _test_redis_client
    _test_redis_client = client

def create_redis_client_from_url(url: str, **kwargs) -> redis.Redis:
    """Create a Redis client from URL, using test client if available."""
    if _test_redis_client is not None:
        return _test_redis_client
    return redis.from_url(url, **kwargs)
