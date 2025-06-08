"""Basic test suite for fundamental operations."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.db_config import get_test_db

@pytest.mark.asyncio(loop_scope="function")
async def test_basic_database_connection():
    """Test the most basic database connection and query."""
    async with get_test_db() as session:
        # Execute a simple query to verify connection
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1, "Basic database connection test failed"

@pytest.mark.asyncio(loop_scope="function")
async def test_table_create_insert_select_drop():
    """Test table creation, data insertion, retrieval, and cleanup."""
    async with get_test_db() as session:
        # 1. Create table
        await session.execute(text("CREATE TABLE IF NOT EXISTS brick_test (id INTEGER PRIMARY KEY, value TEXT)"))
        await session.commit()

        # 2. Insert data
        await session.execute(text("INSERT INTO brick_test (value) VALUES ('hello world')"))
        await session.commit()

        # 3. Retrieve data
        result = await session.execute(text("SELECT value FROM brick_test WHERE id=1"))
        value = result.scalar()
        assert value == 'hello world', f"Expected 'hello world', got {value}"

        # 4. Cleanup
        await session.execute(text("DROP TABLE brick_test"))
        await session.commit()

@pytest.mark.asyncio(loop_scope="function")
async def test_update_row():
    """Test updating a row in the table."""
    async with get_test_db() as session:
        # 1. Create table
        await session.execute(text("CREATE TABLE IF NOT EXISTS brick_test (id INTEGER PRIMARY KEY, value TEXT)"))
        await session.commit()

        # 2. Insert data
        await session.execute(text("INSERT INTO brick_test (value) VALUES ('hello world')"))
        await session.commit()

        # 3. Update data
        await session.execute(text("UPDATE brick_test SET value = 'updated value' WHERE id=1"))
        await session.commit()

        # 4. Retrieve updated data
        result = await session.execute(text("SELECT value FROM brick_test WHERE id=1"))
        value = result.scalar()
        assert value == 'updated value', f"Expected 'updated value', got {value}"

        # 5. Cleanup
        await session.execute(text("DROP TABLE brick_test"))
        await session.commit()

@pytest.mark.asyncio(loop_scope="function")
async def test_delete_row():
    """Test deleting a row from the table."""
    async with get_test_db() as session:
        # 1. Create table
        await session.execute(text("CREATE TABLE IF NOT EXISTS brick_test (id INTEGER PRIMARY KEY, value TEXT)"))
        await session.commit()

        # 2. Insert data
        await session.execute(text("INSERT INTO brick_test (value) VALUES ('hello world')"))
        await session.commit()

        # 3. Delete data
        await session.execute(text("DELETE FROM brick_test WHERE id=1"))
        await session.commit()

        # 4. Verify deletion
        result = await session.execute(text("SELECT value FROM brick_test WHERE id=1"))
        value = result.scalar()
        assert value is None, f"Expected None, got {value}"

        # 5. Cleanup
        await session.execute(text("DROP TABLE brick_test"))
        await session.commit()

@pytest.mark.asyncio(loop_scope="function")
async def test_insert_multiple_rows():
    """Test inserting multiple rows and retrieving them."""
    async with get_test_db() as session:
        # 1. Create table
        await session.execute(text("CREATE TABLE IF NOT EXISTS brick_test (id INTEGER PRIMARY KEY, value TEXT)"))
        await session.commit()

        # 2. Insert multiple rows
        await session.execute(text("INSERT INTO brick_test (value) VALUES ('row1'), ('row2'), ('row3')"))
        await session.commit()

        # 3. Retrieve all rows
        result = await session.execute(text("SELECT value FROM brick_test ORDER BY id"))
        values = result.scalars().all()
        assert values == ['row1', 'row2', 'row3'], f"Expected ['row1', 'row2', 'row3'], got {values}"

        # 4. Cleanup
        await session.execute(text("DROP TABLE brick_test"))
        await session.commit()

@pytest.mark.asyncio(loop_scope="function")
async def test_filter_rows():
    """Test filtering rows using a WHERE clause."""
    async with get_test_db() as session:
        # 1. Create table
        await session.execute(text("CREATE TABLE IF NOT EXISTS brick_test (id INTEGER PRIMARY KEY, value TEXT)"))
        await session.commit()

        # 2. Insert multiple rows
        await session.execute(text("INSERT INTO brick_test (value) VALUES ('row1'), ('row2'), ('row3')"))
        await session.commit()

        # 3. Filter rows
        result = await session.execute(text("SELECT value FROM brick_test WHERE value = 'row2'"))
        value = result.scalar()
        assert value == 'row2', f"Expected 'row2', got {value}"

        # 4. Cleanup
        await session.execute(text("DROP TABLE brick_test"))
        await session.commit()

@pytest.mark.asyncio(loop_scope="function")
async def test_order_rows():
    """Test ordering rows using ORDER BY."""
    async with get_test_db() as session:
        # 1. Create table
        await session.execute(text("CREATE TABLE IF NOT EXISTS brick_test (id INTEGER PRIMARY KEY, value TEXT)"))
        await session.commit()

        # 2. Insert multiple rows
        await session.execute(text("INSERT INTO brick_test (value) VALUES ('row3'), ('row1'), ('row2')"))
        await session.commit()

        # 3. Order rows
        result = await session.execute(text("SELECT value FROM brick_test ORDER BY value"))
        values = result.scalars().all()
        assert values == ['row1', 'row2', 'row3'], f"Expected ['row1', 'row2', 'row3'], got {values}"

        # 4. Cleanup
        await session.execute(text("DROP TABLE brick_test"))
        await session.commit()

@pytest.mark.asyncio(loop_scope="function")
async def test_limit_rows():
    """Test limiting the number of rows returned using LIMIT."""
    async with get_test_db() as session:
        # 1. Create table
        await session.execute(text("CREATE TABLE IF NOT EXISTS brick_test (id INTEGER PRIMARY KEY, value TEXT)"))
        await session.commit()

        # 2. Insert multiple rows
        await session.execute(text("INSERT INTO brick_test (value) VALUES ('row1'), ('row2'), ('row3')"))
        await session.commit()

        # 3. Limit rows
        result = await session.execute(text("SELECT value FROM brick_test ORDER BY id LIMIT 2"))
        values = result.scalars().all()
        assert values == ['row1', 'row2'], f"Expected ['row1', 'row2'], got {values}"

        # 4. Cleanup
        await session.execute(text("DROP TABLE brick_test"))
        await session.commit()

@pytest.mark.asyncio(loop_scope="function")
async def test_count_rows():
    """Test counting rows using COUNT."""
    async with get_test_db() as session:
        # 1. Create table
        await session.execute(text("CREATE TABLE IF NOT EXISTS brick_test (id INTEGER PRIMARY KEY, value TEXT)"))
        await session.commit()

        # 2. Insert multiple rows
        await session.execute(text("INSERT INTO brick_test (value) VALUES ('row1'), ('row2'), ('row3')"))
        await session.commit()

        # 3. Count rows
        result = await session.execute(text("SELECT COUNT(*) FROM brick_test"))
        count = result.scalar()
        assert count == 3, f"Expected 3, got {count}"

        # 4. Cleanup
        await session.execute(text("DROP TABLE brick_test"))
        await session.commit()

@pytest.mark.asyncio(loop_scope="function")
async def test_group_rows():
    """Test grouping rows using GROUP BY."""
    async with get_test_db() as session:
        # 1. Create table
        await session.execute(text("CREATE TABLE IF NOT EXISTS brick_test (id INTEGER PRIMARY KEY, value TEXT)"))
        await session.commit()

        # 2. Insert multiple rows
        await session.execute(text("INSERT INTO brick_test (value) VALUES ('row1'), ('row1'), ('row2')"))
        await session.commit()

        # 3. Group rows
        result = await session.execute(text("SELECT value, COUNT(*) FROM brick_test GROUP BY value"))
        groups = result.fetchall()
        assert groups == [('row1', 2), ('row2', 1)], f"Expected [('row1', 2), ('row2', 1)], got {groups}"

        # 4. Cleanup
        await session.execute(text("DROP TABLE brick_test"))
        await session.commit()

@pytest.mark.asyncio(loop_scope="function")
async def test_join_tables():
    """Test joining two tables using JOIN."""
    async with get_test_db() as session:
        # 1. Create tables
        await session.execute(text("CREATE TABLE IF NOT EXISTS brick_test1 (id INTEGER PRIMARY KEY, value TEXT)"))
        await session.execute(text("CREATE TABLE IF NOT EXISTS brick_test2 (id INTEGER PRIMARY KEY, value TEXT)"))
        await session.commit()

        # 2. Insert rows
        await session.execute(text("INSERT INTO brick_test1 (value) VALUES ('row1'), ('row2')"))
        await session.execute(text("INSERT INTO brick_test2 (value) VALUES ('row1'), ('row3')"))
        await session.commit()

        # 3. Join tables
        result = await session.execute(text("SELECT brick_test1.value FROM brick_test1 JOIN brick_test2 ON brick_test1.value = brick_test2.value"))
        values = result.scalars().all()
        assert values == ['row1'], f"Expected ['row1'], got {values}"

        # 4. Cleanup
        await session.execute(text("DROP TABLE brick_test1"))
        await session.execute(text("DROP TABLE brick_test2"))
        await session.commit()

@pytest.mark.asyncio(loop_scope="function")
async def test_subquery():
    """Test subqueries using a subquery in the WHERE clause."""
    async with get_test_db() as session:
        # 1. Create table
        await session.execute(text("CREATE TABLE IF NOT EXISTS brick_test (id INTEGER PRIMARY KEY, value TEXT)"))
        await session.commit()

        # 2. Insert rows
        await session.execute(text("INSERT INTO brick_test (value) VALUES ('row1'), ('row2'), ('row3')"))
        await session.commit()

        # 3. Use subquery
        result = await session.execute(text("SELECT value FROM brick_test WHERE id IN (SELECT id FROM brick_test WHERE value = 'row1')"))
        values = result.scalars().all()
        assert values == ['row1'], f"Expected ['row1'], got {values}"

        # 4. Cleanup
        await session.execute(text("DROP TABLE brick_test"))
        await session.commit()

@pytest.mark.asyncio(loop_scope="function")
async def test_aggregate_functions():
    """Test using aggregate functions like AVG, MAX, MIN."""
    async with get_test_db() as session:
        # 1. Create table
        await session.execute(text("CREATE TABLE IF NOT EXISTS brick_test (id INTEGER PRIMARY KEY, value INTEGER)"))
        await session.commit()

        # 2. Insert rows
        await session.execute(text("INSERT INTO brick_test (value) VALUES (1), (2), (3)"))
        await session.commit()

        # 3. Use aggregate functions
        result = await session.execute(text("SELECT AVG(value), MAX(value), MIN(value) FROM brick_test"))
        avg, max_val, min_val = result.fetchone()
        assert avg == 2.0, f"Expected 2.0, got {avg}"
        assert max_val == 3, f"Expected 3, got {max_val}"
        assert min_val == 1, f"Expected 1, got {min_val}"

        # 4. Cleanup
        await session.execute(text("DROP TABLE brick_test"))
        await session.commit() 