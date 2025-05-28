import pytest
import redis

from backend.config import settings




def test_redis_connection():
    """Test Redis connection and basic operations."""
    try:
        # Create Redis client
        r = redis.Redis.from_url(settings.REDIS_URL)

        # Test connection
        assert r.ping(), "Redis server is not responding"

        # Test basic operations
        test_key = "test:connection"
        test_value = "Hello Redis!"

        # Set value
        r.set(test_key, test_value)

        # Get value
        retrieved_value = r.get(test_key)
        assert (
            retrieved_value.decode("utf-8") == test_value
        ), "Redis get/set operations failed"

        # Clean up
        r.delete(test_key)

        print("✅ Redis connection test passed!")
        return True

    except redis.ConnectionError as e:
        print(f"❌ Redis connection failed: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure Redis is installed:")
        print("   - macOS: brew install redis")
        print("   - Ubuntu: sudo apt-get install redis-server")
        print(
            "   - Windows: Download from https://github.com/microsoftarchive/redis/releases"
        )
        print("\n2. Make sure Redis server is running:")
        print("   - macOS: brew services start redis")
        print("   - Ubuntu: sudo systemctl start redis-server")
        print("   - Windows: Redis should run as a service")
        print("\n3. Check Redis URL in .env file:")
        print(f"   Current URL: {settings.REDIS_URL}")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    test_redis_connection()
