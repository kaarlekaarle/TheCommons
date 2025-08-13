import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User
from backend.models.poll import Poll
from backend.models.option import Option
from backend.models.vote import Vote
from backend.models.delegation import Delegation
from backend.core.security import get_password_hash


@pytest.mark.asyncio
async def test_activity_feed_structure(async_client: AsyncClient, db_session: AsyncSession):
    """Test that the activity feed returns the correct structure."""
    
    # Create test users
    user1 = User(
        username="testuser1",
        email="test1@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
        is_deleted=False
    )
    user2 = User(
        username="testuser2", 
        email="test2@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
        is_deleted=False
    )
    
    db_session.add(user1)
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)
    
    # Create a test proposal
    poll = Poll(
        title="Test Proposal",
        description="A test proposal",
        created_by=user1.id,
        is_active=True,
        is_deleted=False
    )
    db_session.add(poll)
    await db_session.commit()
    await db_session.refresh(poll)
    
    # Create options
    option_yes = Option(poll_id=poll.id, text="Yes")
    option_no = Option(poll_id=poll.id, text="No")
    db_session.add(option_yes)
    db_session.add(option_no)
    await db_session.commit()
    await db_session.refresh(option_yes)
    await db_session.refresh(option_no)
    
    # Create a vote
    vote = Vote(
        poll_id=poll.id,
        option_id=option_yes.id,
        user_id=user2.id,
        is_deleted=False
    )
    db_session.add(vote)
    await db_session.commit()
    await db_session.refresh(vote)
    
    # Create a delegation
    delegation = Delegation(
        delegator_id=user1.id,
        delegatee_id=user2.id,
        is_deleted=False
    )
    db_session.add(delegation)
    await db_session.commit()
    await db_session.refresh(delegation)
    
    # Test the activity feed
    response = await async_client.get("/api/activity/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3  # Should have at least proposal, vote, and delegation
    
    # Check structure of first item
    first_item = data[0]
    assert "type" in first_item
    assert "id" in first_item
    assert "user" in first_item
    assert "timestamp" in first_item
    assert "details" in first_item
    
    # Check user structure
    user = first_item["user"]
    assert "id" in user
    assert "username" in user
    
    # Check valid types
    valid_types = ["proposal", "vote", "delegation"]
    for item in data:
        assert item["type"] in valid_types


@pytest.mark.asyncio
async def test_activity_feed_ordering(async_client: AsyncClient, db_session: AsyncSession):
    """Test that activity feed items are ordered by timestamp (newest first)."""
    
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com", 
        hashed_password=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
        is_deleted=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create two proposals with different timestamps
    from datetime import datetime, timedelta
    
    # Older proposal
    old_poll = Poll(
        title="Older Proposal",
        description="This should appear second",
        created_by=user.id,
        created_at=datetime.utcnow() - timedelta(hours=2),
        is_active=True,
        is_deleted=False
    )
    
    # Newer proposal  
    new_poll = Poll(
        title="Newer Proposal",
        description="This should appear first",
        created_by=user.id,
        created_at=datetime.utcnow() - timedelta(hours=1),
        is_active=True,
        is_deleted=False
    )
    
    db_session.add(old_poll)
    db_session.add(new_poll)
    await db_session.commit()
    await db_session.refresh(old_poll)
    await db_session.refresh(new_poll)
    
    # Test the activity feed
    response = await async_client.get("/api/activity/")
    assert response.status_code == 200
    
    data = response.json()
    
    # Find our test proposals
    newer_found = False
    older_found = False
    
    for item in data:
        if item["type"] == "proposal" and "Newer Proposal" in item["details"]:
            newer_found = True
        elif item["type"] == "proposal" and "Older Proposal" in item["details"]:
            older_found = True
            
        # If we found the older one, we should have already found the newer one
        if older_found and not newer_found:
            pytest.fail("Older proposal appeared before newer proposal")
    
    assert newer_found, "Newer proposal not found in feed"
    assert older_found, "Older proposal not found in feed"


@pytest.mark.asyncio
async def test_activity_feed_limit(async_client: AsyncClient, db_session: AsyncSession):
    """Test that the limit parameter works correctly."""
    
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
        is_deleted=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create multiple proposals
    for i in range(25):
        poll = Poll(
            title=f"Proposal {i}",
            description=f"Test proposal {i}",
            created_by=user.id,
            is_active=True,
            is_deleted=False
        )
        db_session.add(poll)
    
    await db_session.commit()
    
    # Test default limit (20)
    response = await async_client.get("/api/activity/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 20
    
    # Test custom limit
    response = await async_client.get("/api/activity/?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5


@pytest.mark.asyncio
async def test_activity_feed_public_access(async_client: AsyncClient):
    """Test that the activity feed is accessible without authentication."""
    
    response = await async_client.get("/api/activity/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
