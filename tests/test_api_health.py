import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.models.option import Option
from backend.models.poll import Poll
from backend.models.user import User
from backend.models.vote import Vote
from tests.utils import (
    create_test_user,
    create_test_poll,
    create_test_option,
    create_test_vote,
)

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_database_health(client: AsyncClient, db_session: AsyncSession):
    """Test the database health check endpoint."""
    response = await client.get("/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_database_health_with_error(client: AsyncClient, db_session: AsyncSession):
    """Test the database health check endpoint when there's an error."""
    # Simulate a database error by executing an invalid query
    with pytest.raises(Exception):
        await db_session.execute(text("SELECT * FROM nonexistent_table"))

    response = await client.get("/health/db")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database connection error"}

@pytest.mark.asyncio
async def test_database_health_with_data(client: AsyncClient, db_session: AsyncSession):
    """Test the database health check endpoint with data."""
    # Create test data using utility functions
    user = await create_test_user(db_session)
    poll = await create_test_poll(db_session, user)
    option = await create_test_option(db_session, poll)
    vote = await create_test_vote(db_session, user, poll, option)

    response = await client.get("/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
