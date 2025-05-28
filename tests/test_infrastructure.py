"""Test infrastructure configuration."""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.db_config import test_engine, get_test_db
from tests.redis_config import get_test_redis, TestRedisClient

@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection and basic operations."""
    async with get_test_db() as session:
        # Test connection
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1, "Database connection failed"
        
        # Test transaction
        await session.execute(text("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)"))
        await session.commit()
        
        # Verify table creation
        result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"))
        assert result.scalar() == "test_table", "Table creation failed"
        
        # Clean up
        await session.execute(text("DROP TABLE test_table"))
        await session.commit()

@pytest.mark.asyncio
async def test_database_isolation():
    """Test database isolation between tests."""
    async with get_test_db() as session1:
        # Create and populate a test table
        await session1.execute(text("CREATE TABLE IF NOT EXISTS isolation_test (id INTEGER PRIMARY KEY, value TEXT)"))
        await session1.execute(text("INSERT INTO isolation_test (value) VALUES ('test1')"))
        await session1.commit()
        
        # Verify data in first session
        result = await session1.execute(text("SELECT value FROM isolation_test"))
        assert result.scalar() == "test1", "Data not found in first session"
        
        # Create a new session and verify it's isolated
        async with get_test_db() as session2:
            result = await session2.execute(text("SELECT value FROM isolation_test"))
            assert result.scalar() is None, "Data leaked between sessions"
        
        # Clean up
        await session1.execute(text("DROP TABLE isolation_test"))
        await session1.commit()

@pytest.mark.asyncio
async def test_redis_connection():
    """Test Redis connection and basic operations."""
    async with get_test_redis() as client:
        # Test basic operations
        await client.client.set("test_key", "test_value")
        value = await client.client.get("test_key")
        assert value == b"test_value", "Redis get/set operations failed"
        
        # Test flush
        await client.flush()
        value = await client.client.get("test_key")
        assert value is None, "Redis flush failed"

@pytest.mark.asyncio
async def test_redis_isolation():
    """Test Redis isolation between tests."""
    # First test
    async with get_test_redis() as client1:
        await client1.client.set("isolation_key", "test1")
        value = await client1.client.get("isolation_key")
        assert value == b"test1", "Data not found in first test"
    
    # Second test (should be isolated)
    async with get_test_redis() as client2:
        value = await client2.client.get("isolation_key")
        assert value is None, "Data leaked between tests"

@pytest.mark.asyncio
async def test_integrated_operations():
    """Test integrated database and Redis operations."""
    async with get_test_db() as session:
        # Database operation
        await session.execute(text("CREATE TABLE IF NOT EXISTS integrated_test (id INTEGER PRIMARY KEY, value TEXT)"))
        await session.execute(text("INSERT INTO integrated_test (value) VALUES ('db_value')"))
        await session.commit()
        
        # Redis operation
        async with get_test_redis() as client:
            await client.client.set("integrated_key", "redis_value")
            
            # Verify both operations
            db_result = await session.execute(text("SELECT value FROM integrated_test"))
            redis_value = await client.client.get("integrated_key")
            
            assert db_result.scalar() == "db_value", "Database operation failed"
            assert redis_value == b"redis_value", "Redis operation failed"
            
            # Clean up
            await session.execute(text("DROP TABLE integrated_test"))
            await session.commit()
            await client.flush() 