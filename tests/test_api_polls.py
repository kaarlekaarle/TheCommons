import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from backend.main import app
from backend.models.option import Option
from backend.models.poll import Poll
from backend.models.user import User

client = TestClient(app)


@pytest.mark.asyncio
async def test_create_poll(db_session: AsyncSession, client: Any) -> None:
    """Test creating a new poll."""
    # Fetch the test user created by the client fixture
    result = await db_session.execute(
        select(User).where(User.username == client.test_user.username)
    )
    user = result.scalar_one()

    poll_data = {"title": "Test Poll", "description": "Test Description"}
    response = await client.post("/api/polls/", json=poll_data)
    assert response.status_code == 201 or response.status_code == 200
    assert response.json()["title"] == poll_data["title"]
    assert response.json()["description"] == poll_data["description"]
    assert response.json()["created_by"] == user.id
    # Optionally, check for 'options' if your API includes them in the response
    # assert "options" in response.json()


@pytest.mark.asyncio
async def test_get_poll(db_session: AsyncSession, client: Any) -> None:
    """Test getting a specific poll."""
    # Create a test user
    unique_id = str(uuid.uuid4())
    user = User(
        email=f"testuser_{unique_id}@example.com",
        username=f"testuser_{unique_id}",
        hashed_password="test_password",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create a test poll
    poll = Poll(title="Test Poll", description="Test Description", created_by=user.id)
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)

    # Test getting the poll
    response = await client.get(f"/api/polls/{poll.id}")
    assert response.status_code == 200
    assert response.json()["id"] == poll.id
    assert response.json()["title"] == poll.title
    assert response.json()["description"] == poll.description
    assert response.json()["created_by"] == user.id


@pytest.mark.asyncio
async def test_get_poll_not_found(client: Any) -> None:
    """Test getting a non-existent poll."""
    response = await client.get("/api/polls/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Poll not found"}


@pytest.mark.asyncio
async def test_get_polls(db_session: AsyncSession, client: Any) -> None:
    """Test getting all polls."""
    # Create a test user
    unique_id = str(uuid.uuid4())
    user = User(
        email=f"testuser_{unique_id}@example.com",
        username=f"testuser_{unique_id}",
        hashed_password="test_password",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create some test polls
    polls = []
    for i in range(3):
        poll = Poll(
            title=f"Test Poll {i}",
            description=f"Test Description {i}",
            created_by=user.id,
        )
        db_session.add(poll)
        await db_session.commit()
        await db_session.refresh(poll)
        polls.append(poll)
        # Add options for each poll
        for j in range(2):
            option = Option(text=f"Option {j}", poll_id=poll.id)
            db_session.add(option)
        await db_session.commit()

    # Test getting all polls
    response = await client.get("/api/polls/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    for poll in polls:
        assert any(p["id"] == poll.id for p in data)
